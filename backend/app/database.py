import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DATABASE_PATH = DATA_DIRECTORY / "expedia-lite.db"
INITIAL_SEED_NAME = "initial-csv-data"

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS hotels (
        hotel_id TEXT PRIMARY KEY,
        hotel_name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        nightly_rate_usd REAL NOT NULL CHECK (nightly_rate_usd >= 0)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS trips (
        trip_id TEXT PRIMARY KEY,
        hotel_id TEXT NOT NULL,
        trip_name TEXT NOT NULL,
        check_in TEXT NOT NULL,
        check_out TEXT NOT NULL,
        CHECK (check_out > check_in),
        FOREIGN KEY (hotel_id) REFERENCES hotels (hotel_id)
            ON UPDATE RESTRICT ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS bookings (
        booking_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        trip_id TEXT NOT NULL,
        booked_on TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled')),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
            ON UPDATE RESTRICT ON DELETE RESTRICT,
        FOREIGN KEY (trip_id) REFERENCES trips (trip_id)
            ON UPDATE RESTRICT ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS booking_id_sequence (
        singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
        next_number INTEGER NOT NULL CHECK (next_number > 0)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS seed_metadata (
        seed_name TEXT PRIMARY KEY,
        completed_at TEXT NOT NULL
    )
    """,
)

CSV_HEADERS = {
    "hotels.csv": ("hotel_id", "hotel_name", "city", "state", "nightly_rate_usd"),
    "trips.csv": ("trip_id", "hotel_id", "trip_name", "check_in", "check_out"),
    "users.csv": ("user_id", "display_name"),
    "bookings.csv": ("booking_id", "user_id", "trip_id", "booked_on", "status"),
}


def connect_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> sqlite3.Connection:
    """Open an Expedia Lite database with foreign keys enforced."""

    resolved_path = Path(database_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
    if foreign_keys_enabled != 1:
        connection.close()
        raise RuntimeError("SQLite foreign key enforcement could not be enabled.")

    return connection


def _read_csv_rows(
    data_directory: Path,
    filename: str,
) -> list[dict[str, str]]:
    path = data_directory / filename
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        expected_headers = CSV_HEADERS[filename]
        actual_headers = tuple(reader.fieldnames or ())
        if actual_headers != expected_headers:
            raise ValueError(
                f"{filename} headers must be {expected_headers}, got {actual_headers}."
            )
        return list(reader)


def _seed_from_csv(connection: sqlite3.Connection, data_directory: Path) -> None:
    hotels = _read_csv_rows(data_directory, "hotels.csv")
    trips = _read_csv_rows(data_directory, "trips.csv")
    users = _read_csv_rows(data_directory, "users.csv")
    bookings = _read_csv_rows(data_directory, "bookings.csv")

    connection.executemany(
        """
        INSERT INTO hotels (
            hotel_id, hotel_name, city, state, nightly_rate_usd
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                row["hotel_id"],
                row["hotel_name"],
                row["city"],
                row["state"],
                float(row["nightly_rate_usd"]),
            )
            for row in hotels
        ],
    )
    booking_numbers = []
    for row in bookings:
        booking_id = row["booking_id"]
        if not booking_id.startswith("B") or not booking_id[1:].isdigit():
            raise ValueError(f"Invalid supplied booking ID: {booking_id!r}.")
        booking_numbers.append(int(booking_id[1:]))

    connection.execute(
        "INSERT INTO booking_id_sequence (singleton, next_number) VALUES (1, ?)",
        (max(booking_numbers, default=0) + 1,),
    )
    connection.executemany(
        "INSERT INTO users (user_id, display_name) VALUES (?, ?)",
        [(row["user_id"], row["display_name"]) for row in users],
    )
    connection.executemany(
        """
        INSERT INTO trips (
            trip_id, hotel_id, trip_name, check_in, check_out
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                row["trip_id"],
                row["hotel_id"],
                row["trip_name"],
                row["check_in"],
                row["check_out"],
            )
            for row in trips
        ],
    )
    connection.executemany(
        """
        INSERT INTO bookings (
            booking_id, user_id, trip_id, booked_on, status
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                row["booking_id"],
                row["user_id"],
                row["trip_id"],
                row["booked_on"],
                row["status"],
            )
            for row in bookings
        ],
    )


def initialize_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    data_directory: str | Path = DATA_DIRECTORY,
) -> bool:
    """Create the schema and seed CSV rows once for this database file.

    Returns True only when this call applies the initial CSV seed.
    """

    connection = connect_database(database_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)

        seed_exists = connection.execute(
            "SELECT 1 FROM seed_metadata WHERE seed_name = ?",
            (INITIAL_SEED_NAME,),
        ).fetchone()
        if seed_exists is not None:
            connection.commit()
            return False

        _seed_from_csv(connection, Path(data_directory))
        connection.execute(
            "INSERT INTO seed_metadata (seed_name, completed_at) VALUES (?, ?)",
            (INITIAL_SEED_NAME, datetime.now(timezone.utc).isoformat()),
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
