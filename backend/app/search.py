import sqlite3

from .domain import build_stay_record, escape_like_pattern, normalize_search_term


class InvalidSearchQueryError(ValueError):
    pass


def search_stays(
    connection: sqlite3.Connection,
    query: str,
) -> list[dict[str, str | int | float]]:
    """Search joined stays by partial hotel name or exact city."""

    normalized_query = normalize_search_term(query)
    if not normalized_query:
        raise InvalidSearchQueryError("Enter a hotel name or city to search.")

    hotel_name_pattern = f"%{escape_like_pattern(normalized_query)}%"
    rows = connection.execute(
        """
        SELECT
            trips.trip_id,
            trips.trip_name,
            trips.check_in,
            trips.check_out,
            hotels.hotel_id,
            hotels.hotel_name,
            hotels.city,
            hotels.state,
            hotels.nightly_rate_usd
        FROM trips
        JOIN hotels ON hotels.hotel_id = trips.hotel_id
        WHERE hotels.hotel_name COLLATE NOCASE LIKE ? ESCAPE '\\'
           OR hotels.city = ? COLLATE NOCASE
        ORDER BY trips.trip_id
        """,
        (hotel_name_pattern, normalized_query),
    ).fetchall()

    return [
        build_stay_record(
            trip_id=row["trip_id"],
            trip_name=row["trip_name"],
            hotel_id=row["hotel_id"],
            hotel_name=row["hotel_name"],
            city=row["city"],
            state=row["state"],
            check_in=row["check_in"],
            check_out=row["check_out"],
            nightly_rate_usd=row["nightly_rate_usd"],
        )
        for row in rows
    ]
