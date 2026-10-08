import json
import re
import sqlite3
from collections.abc import Callable


ALLOWED_TABLES = frozenset(
    {
        "saved_hotels",
        "saved_hotel_zips",
        "demo_hotel_nights",
    }
)
ALLOWED_FUNCTIONS = frozenset(
    {
        "abs",
        "avg",
        "coalesce",
        "count",
        "date",
        "ifnull",
        "julianday",
        "length",
        "lower",
        "max",
        "min",
        "nullif",
        "printf",
        "round",
        "strftime",
        "substr",
        "substring",
        "sum",
        "upper",
    }
)
MAX_GENERATED_SQL_LENGTH = 2_000
MAX_QUERY_RESULT_ROWS = 50
MAX_QUERY_RESULT_COLUMNS = 20
MAX_QUERY_RESULT_JSON_BYTES = 50_000
QUERY_PROGRESS_INTERVAL = 1_000
MAX_QUERY_PROGRESS_CALLBACKS = 100


class GeneratedQueryRejectedError(ValueError):
    pass


def _reject(message: str) -> GeneratedQueryRejectedError:
    return GeneratedQueryRejectedError(f"Generated query was rejected: {message}")


def _normalized_select(sql: str) -> str:
    normalized = sql.strip()
    if not normalized:
        raise _reject("the SQL was empty.")
    if len(normalized) > MAX_GENERATED_SQL_LENGTH:
        raise _reject(
            f"the SQL exceeded {MAX_GENERATED_SQL_LENGTH} characters."
        )
    if ";" in normalized:
        raise _reject("multiple statements and semicolons are not allowed.")
    if re.search(r"--|/\*|\*/", normalized):
        raise _reject("SQL comments are not allowed.")
    if re.match(r"select\b", normalized, re.IGNORECASE) is None:
        raise _reject("only one read-only SELECT statement is allowed.")
    return normalized


def _authorizer(
    read_tables: set[str],
    rejection: list[str],
) -> Callable[[int, str | None, str | None, str | None, str | None], int]:
    allowed_actions = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
    recursive_action = getattr(sqlite3, "SQLITE_RECURSIVE", None)
    if recursive_action is not None:
        allowed_actions.add(recursive_action)

    def authorize(
        action: int,
        first: str | None,
        second: str | None,
        _database: str | None,
        _trigger: str | None,
    ) -> int:
        if action not in allowed_actions:
            rejection.append("the statement requested a disallowed SQLite operation.")
            return sqlite3.SQLITE_DENY

        if action == sqlite3.SQLITE_READ:
            table = (first or "").lower()
            if table not in ALLOWED_TABLES:
                rejection.append(f"table {table or '<unknown>'!r} is not authorized.")
                return sqlite3.SQLITE_DENY
            read_tables.add(table)

        if action == sqlite3.SQLITE_FUNCTION:
            function = (second or first or "").lower()
            if function not in ALLOWED_FUNCTIONS:
                rejection.append(f"function {function or '<unknown>'!r} is not authorized.")
                return sqlite3.SQLITE_DENY

        return sqlite3.SQLITE_OK

    return authorize


def validate_generated_query(
    connection: sqlite3.Connection,
    sql: str,
) -> str:
    """Compile one generated SELECT under a deny-by-default SQLite authorizer."""

    normalized = _normalized_select(sql)
    read_tables: set[str] = set()
    rejection: list[str] = []
    connection.set_authorizer(_authorizer(read_tables, rejection))
    try:
        connection.execute(f"EXPLAIN QUERY PLAN {normalized}").fetchall()
    except sqlite3.DatabaseError:
        if rejection:
            raise _reject(rejection[0]) from None
        raise _reject("the SQL was invalid.") from None
    finally:
        connection.set_authorizer(None)

    if not read_tables:
        raise _reject("the query did not read an authorized saved-hotel table.")
    return normalized


def execute_validated_query(
    connection: sqlite3.Connection,
    sql: str,
) -> list[dict[str, str | int | float | None]]:
    """Validate, bound, and execute generated SQL without permitting mutations."""

    normalized = validate_generated_query(connection, sql)
    read_tables: set[str] = set()
    rejection: list[str] = []
    progress_callbacks = 0
    work_limit_reached = False

    def progress() -> int:
        nonlocal progress_callbacks, work_limit_reached
        progress_callbacks += 1
        if progress_callbacks > MAX_QUERY_PROGRESS_CALLBACKS:
            work_limit_reached = True
            return 1
        return 0

    connection.set_authorizer(_authorizer(read_tables, rejection))
    connection.set_progress_handler(progress, QUERY_PROGRESS_INTERVAL)
    try:
        cursor = connection.execute(
            f"SELECT * FROM ({normalized}) AS generated_result "
            f"LIMIT {MAX_QUERY_RESULT_ROWS + 1}"
        )
        description = cursor.description or ()
        if len(description) > MAX_QUERY_RESULT_COLUMNS:
            raise _reject(
                f"the result exceeded {MAX_QUERY_RESULT_COLUMNS} columns."
            )
        rows = cursor.fetchall()
    except GeneratedQueryRejectedError:
        raise
    except sqlite3.DatabaseError:
        if work_limit_reached:
            raise _reject("the query exceeded the work limit.") from None
        if rejection:
            raise _reject(rejection[0]) from None
        raise _reject("the query could not be executed safely.") from None
    finally:
        connection.set_progress_handler(None, 0)
        connection.set_authorizer(None)

    if len(rows) > MAX_QUERY_RESULT_ROWS:
        raise _reject(
            f"the result exceeded {MAX_QUERY_RESULT_ROWS} rows."
        )

    columns = [column[0] for column in description]
    records: list[dict[str, str | int | float | None]] = []
    for row in rows:
        record: dict[str, str | int | float | None] = {}
        for column, value in zip(columns, row, strict=True):
            if value is not None and not isinstance(value, (str, int, float)):
                raise _reject("the result contained an unsupported value type.")
            record[column] = value
        records.append(record)

    serialized = json.dumps(records, ensure_ascii=True, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > MAX_QUERY_RESULT_JSON_BYTES:
        raise _reject(
            f"the result exceeded {MAX_QUERY_RESULT_JSON_BYTES} JSON bytes."
        )
    return records
