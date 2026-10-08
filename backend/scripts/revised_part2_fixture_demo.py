"""Print a labeled rejected-query fixture without touching the assignment database."""

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.database import DATA_DIRECTORY, connect_database, initialize_database  # noqa: E402
from app.hotel_insights import answer_saved_hotel_question  # noqa: E402


FIXTURE_PATH = (
    BACKEND_DIRECTORY
    / "tests"
    / "fixtures"
    / "revised_part2_fixed_sample.json"
)
MODEL_LABEL = "fixture/provider-not-called"


def seed_fixture(connection: sqlite3.Connection, sample: dict[str, object]) -> None:
    for hotel in sample["hotels"]:
        cursor = connection.execute(
            """
            INSERT INTO saved_hotels (
                provider_place_id, hotel_name, address, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                hotel["provider_place_id"],
                hotel["hotel_name"],
                hotel["address"],
                hotel["latitude"],
                hotel["longitude"],
            ),
        )
        saved_hotel_id = cursor.lastrowid
        connection.executemany(
            "INSERT INTO saved_hotel_zips (saved_hotel_id, searched_zip) VALUES (?, ?)",
            [(saved_hotel_id, zip_code) for zip_code in hotel["searched_zips"]],
        )
        connection.executemany(
            """
            INSERT INTO demo_hotel_nights (
                saved_hotel_id, night_date, nightly_rate_cents, rooms_available
            ) VALUES (?, ?, ?, ?)
            """,
            [
                (saved_hotel_id, night_date, rate, rooms)
                for night_date, rate, rooms in hotel["nights"]
            ],
        )
    connection.commit()


def snapshot(connection: sqlite3.Connection) -> dict[str, list[list[object]]]:
    tables = (
        "hotels",
        "users",
        "trips",
        "bookings",
        "booking_id_sequence",
        "seed_metadata",
        "saved_hotels",
        "saved_hotel_zips",
        "demo_hotel_nights",
    )
    return {
        table: [list(row) for row in connection.execute(f"SELECT * FROM {table}")]
        for table in tables
    }


def main() -> None:
    sample = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    second_request_calls = 0

    with tempfile.TemporaryDirectory(prefix="expedia-lite-rejected-query-") as directory:
        database_path = Path(directory) / "fixture.db"
        initialize_database(database_path, DATA_DIRECTORY)
        connection = connect_database(database_path)
        try:
            seed_fixture(connection, sample)
            before = snapshot(connection)

            def sql_requester(_question: str):
                return (
                    {
                        "status": "query",
                        "sql": "DELETE FROM saved_hotels",
                    },
                    MODEL_LABEL,
                )

            def answer_requester(*_args):
                nonlocal second_request_calls
                second_request_calls += 1
                raise AssertionError("Rejected SQL must not reach request two")

            result = answer_saved_hotel_question(
                connection,
                "FIXTURE ONLY: try to delete the saved hotels.",
                sql_requester=sql_requester,
                answer_requester=answer_requester,
            )
            after = snapshot(connection)
        finally:
            connection.close()

    print("FIXTURE ONLY - no live provider was called")
    print("Proposed SQL: DELETE FROM saved_hotels")
    print(f"Pipeline status: {result['status']}")
    print(f"Validation: {result['trace']['validation_status']}")
    print(f"Generated query executed: {result['trace']['query_executed']}")
    print(f"Second model request calls: {second_request_calls}")
    print(f"Protected data unchanged: {before == after}")
    print(f"Temporary database removed: {not database_path.exists()}")


if __name__ == "__main__":
    main()
