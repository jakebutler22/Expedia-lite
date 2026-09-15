import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from app.database import connect_database, initialize_database


DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"


def test_new_database_seeds_all_csv_rows_with_ids_intact(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia-lite.db"

    assert initialize_database(database_path, DATA_DIRECTORY) is True

    with closing(connect_database(database_path)) as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("hotels", "trips", "users", "bookings")
        }
        hotel_ids = [
            row[0]
            for row in connection.execute(
                "SELECT hotel_id FROM hotels ORDER BY hotel_id"
            )
        ]
        trip_ids = [
            row[0]
            for row in connection.execute(
                "SELECT trip_id FROM trips ORDER BY trip_id"
            )
        ]
        user_ids = [
            row[0]
            for row in connection.execute(
                "SELECT user_id FROM users ORDER BY user_id"
            )
        ]
        booking_ids = [
            row[0]
            for row in connection.execute(
                "SELECT booking_id FROM bookings ORDER BY booking_id"
            )
        ]

    assert counts == {"hotels": 8, "trips": 12, "users": 6, "bookings": 6}
    assert hotel_ids == [f"H{number:03d}" for number in range(1, 9)]
    assert trip_ids == [f"T{number:03d}" for number in range(1, 13)]
    assert user_ids == [f"U{number:03d}" for number in range(1, 7)]
    assert booking_ids == [f"B{number:03d}" for number in range(1, 7)]


def test_seeding_twice_does_not_duplicate_rows(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia-lite.db"

    assert initialize_database(database_path, DATA_DIRECTORY) is True
    assert initialize_database(database_path, tmp_path / "missing-csv-directory") is False

    with closing(connect_database(database_path)) as connection:
        counts = [
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("hotels", "trips", "users", "bookings")
        ]

    assert counts == [8, 12, 6, 6]


def test_second_seed_does_not_restore_deleted_booking(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia-lite.db"
    initialize_database(database_path, DATA_DIRECTORY)

    with closing(connect_database(database_path)) as connection:
        connection.execute("DELETE FROM bookings WHERE booking_id = ?", ("B003",))
        connection.commit()

    assert initialize_database(database_path, DATA_DIRECTORY) is False

    with closing(connect_database(database_path)) as connection:
        deleted_booking = connection.execute(
            "SELECT booking_id FROM bookings WHERE booking_id = ?", ("B003",)
        ).fetchone()
        booking_count = connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]

    assert deleted_booking is None
    assert booking_count == 5


def test_second_seed_does_not_erase_new_booking(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia-lite.db"
    initialize_database(database_path, DATA_DIRECTORY)

    new_booking = ("B007", "U006", "T012", "2026-09-14", "confirmed")
    with closing(connect_database(database_path)) as connection:
        connection.execute(
            """
            INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            new_booking,
        )
        connection.commit()

    assert initialize_database(database_path, DATA_DIRECTORY) is False

    with closing(connect_database(database_path)) as connection:
        stored_booking = connection.execute(
            """
            SELECT booking_id, user_id, trip_id, booked_on, status
            FROM bookings
            WHERE booking_id = ?
            """,
            ("B007",),
        ).fetchone()
        booking_count = connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]

    assert tuple(stored_booking) == new_booking
    assert booking_count == 7


def test_cancelled_booking_still_exists_after_reseeding(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia-lite.db"
    initialize_database(database_path, DATA_DIRECTORY)

    with closing(connect_database(database_path)) as connection:
        connection.execute(
            "UPDATE bookings SET status = ? WHERE booking_id = ?",
            ("cancelled", "B003"),
        )
        connection.commit()

    assert initialize_database(database_path, DATA_DIRECTORY) is False

    with closing(connect_database(database_path)) as connection:
        booking = connection.execute(
            "SELECT booking_id, status FROM bookings WHERE booking_id = ?", ("B003",)
        ).fetchone()

    assert tuple(booking) == ("B003", "cancelled")


def test_foreign_keys_reject_booking_with_unknown_trip(tmp_path: Path) -> None:
    database_path = tmp_path / "expedia-lite.db"
    initialize_database(database_path, DATA_DIRECTORY)

    with closing(connect_database(database_path)) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("B007", "U001", "T999", "2026-09-14", "confirmed"),
            )

        connection.rollback()
