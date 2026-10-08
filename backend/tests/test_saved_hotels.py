from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

from app.database import connect_database, initialize_database


DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"
FIXED_NIGHT_DATES = [
    "2026-10-10",
    "2026-10-11",
    "2026-10-12",
    "2026-10-13",
    "2026-10-14",
]
TEST_CREDENTIAL = "saved-hotel-test-key-never-return"

PROVIDER_HOTEL = {
    "place_id": "provider-hotel-1",
    "name": "Provider Hotel",
    "latitude": 42.358,
    "longitude": -71.061,
    "formatted_address": "1 Provider Way, Boston, MA 02108",
}

SECOND_PROVIDER_HOTEL = {
    "place_id": "provider-hotel-2",
    "name": "Second Provider Hotel",
    "latitude": 40.804,
    "longitude": -77.86,
    "formatted_address": "2 Provider Way, State College, PA 16802",
}

ASSIGNMENT_ONE_QUERIES = {
    "hotels": "SELECT * FROM hotels ORDER BY hotel_id",
    "trips": "SELECT * FROM trips ORDER BY trip_id",
    "users": "SELECT * FROM users ORDER BY user_id",
    "bookings": "SELECT * FROM bookings ORDER BY booking_id",
    "booking_id_sequence": (
        "SELECT * FROM booking_id_sequence ORDER BY singleton"
    ),
    "seed_metadata": "SELECT * FROM seed_metadata ORDER BY seed_name",
}


def save_hotel(
    client: TestClient,
    searched_zip: str = "02108",
    hotel: dict[str, object] = PROVIDER_HOTEL,
):
    return client.post(
        "/api/saved-hotels",
        json={"searched_zip": searched_zip, "hotel": hotel},
    )


def assert_no_credential_fields(response_text: str) -> None:
    assert TEST_CREDENTIAL not in response_text
    assert "GEOAPIFY_API_KEY" not in response_text
    assert "apiKey" not in response_text


def assignment_one_snapshot(connection) -> dict[str, list[tuple[object, ...]]]:
    """Capture every preserved Assignment 1 value, not only table counts."""

    return {
        table: [tuple(row) for row in connection.execute(query).fetchall()]
        for table, query in ASSIGNMENT_ONE_QUERIES.items()
    }


def test_local_storage_schema_enforces_defaults_keys_and_relationships(
    client: TestClient,
    database_path: Path,
) -> None:
    assert client.get("/api/health").status_code == 200
    with closing(connect_database(database_path)) as connection:
        saved_hotel_columns = {
            row["name"]: row for row in connection.execute(
                "PRAGMA table_info(saved_hotels)"
            )
        }
        zip_columns = {
            row["name"]: row for row in connection.execute(
                "PRAGMA table_info(saved_hotel_zips)"
            )
        }
        night_columns = {
            row["name"]: row for row in connection.execute(
                "PRAGMA table_info(demo_hotel_nights)"
            )
        }
        zip_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(saved_hotel_zips)"
        ).fetchall()
        night_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(demo_hotel_nights)"
        ).fetchall()

    assert set(saved_hotel_columns) == {
        "saved_hotel_id",
        "provider_place_id",
        "hotel_name",
        "address",
        "latitude",
        "longitude",
    }
    assert saved_hotel_columns["saved_hotel_id"]["pk"] == 1
    assert saved_hotel_columns["provider_place_id"]["notnull"] == 1
    assert zip_columns["saved_hotel_id"]["pk"] == 1
    assert zip_columns["searched_zip"]["pk"] == 2
    assert night_columns["saved_hotel_id"]["pk"] == 1
    assert night_columns["night_date"]["pk"] == 2
    assert night_columns["nightly_rate_cents"]["dflt_value"] == "10000"
    assert night_columns["rooms_available"]["dflt_value"] == "20"
    assert [(row["table"], row["on_delete"]) for row in zip_foreign_keys] == [
        ("saved_hotels", "CASCADE")
    ]
    assert [(row["table"], row["on_delete"]) for row in night_foreign_keys] == [
        ("saved_hotels", "CASCADE")
    ]


def test_save_creates_exact_fixed_nights_defaults_and_leading_zero_zip(
    client: TestClient,
    database_path: Path,
) -> None:
    response = save_hotel(client)

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "place_id": "provider-hotel-1",
        "name": "Provider Hotel",
        "address": "1 Provider Way, Boston, MA 02108",
        "latitude": 42.358,
        "longitude": -71.061,
        "searched_zips": ["02108"],
        "nights": [
            {
                "date": night_date,
                "nightly_rate_cents": 10_000,
                "rooms_available": 20,
            }
            for night_date in FIXED_NIGHT_DATES
        ],
    }
    assert_no_credential_fields(response.text)

    with closing(connect_database(database_path)) as connection:
        stored_hotel = connection.execute(
            """
            SELECT saved_hotel_id, provider_place_id, hotel_name, address,
                   latitude, longitude
            FROM saved_hotels
            """
        ).fetchone()
        stored_zip = connection.execute(
            """
            SELECT searched_zip
            FROM saved_hotel_zips
            WHERE saved_hotel_id = ?
            """,
            (stored_hotel["saved_hotel_id"],),
        ).fetchone()["searched_zip"]
        stored_nights = connection.execute(
            """
            SELECT night_date, nightly_rate_cents, rooms_available
            FROM demo_hotel_nights
            WHERE saved_hotel_id = ?
            ORDER BY night_date
            """,
            (stored_hotel["saved_hotel_id"],),
        ).fetchall()

    assert dict(stored_hotel) == {
        "saved_hotel_id": stored_hotel["saved_hotel_id"],
        "provider_place_id": "provider-hotel-1",
        "hotel_name": "Provider Hotel",
        "address": "1 Provider Way, Boston, MA 02108",
        "latitude": 42.358,
        "longitude": -71.061,
    }
    assert stored_zip == "02108"
    assert [tuple(night) for night in stored_nights] == [
        (night_date, 10_000, 20) for night_date in FIXED_NIGHT_DATES
    ]


def test_repeat_save_preserves_manual_values_and_all_zip_associations(
    client: TestClient,
    database_path: Path,
) -> None:
    assert save_hotel(client, "02108").status_code == 201

    with closing(connect_database(database_path)) as connection:
        connection.execute(
            """
            UPDATE demo_hotel_nights
            SET nightly_rate_cents = ?, rooms_available = ?
            WHERE night_date = ?
            """,
            (12_345, 7, "2026-10-12"),
        )
        connection.commit()

    second_save = save_hotel(client, "16802")
    third_save = save_hotel(client, "02108")

    assert second_save.status_code == 201
    assert third_save.status_code == 201
    assert second_save.json()["searched_zips"] == ["02108", "16802"]
    edited_night = next(
        night
        for night in third_save.json()["nights"]
        if night["date"] == "2026-10-12"
    )
    assert edited_night == {
        "date": "2026-10-12",
        "nightly_rate_cents": 12_345,
        "rooms_available": 7,
    }

    with closing(connect_database(database_path)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM saved_hotels"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM saved_hotel_zips"
        ).fetchone()[0] == 2
        assert connection.execute(
            "SELECT COUNT(*) FROM demo_hotel_nights"
        ).fetchone()[0] == 5
        stored_zips = [
            row["searched_zip"]
            for row in connection.execute(
                "SELECT searched_zip FROM saved_hotel_zips ORDER BY searched_zip"
            )
        ]
        stored_night = connection.execute(
            """
            SELECT nightly_rate_cents, rooms_available
            FROM demo_hotel_nights
            WHERE night_date = ?
            """,
            ("2026-10-12",),
        ).fetchone()

    assert stored_zips == ["02108", "16802"]
    assert tuple(stored_night) == (12_345, 7)


def test_lookup_returns_clear_empty_result_and_saved_records(
    client: TestClient,
) -> None:
    empty_response = client.get("/api/saved-hotels", params={"zip": "02108"})

    assert empty_response.status_code == 200
    assert empty_response.json() == {"zip": "02108", "count": 0, "hotels": []}

    assert save_hotel(client, "02108").status_code == 201
    populated_response = client.get(
        "/api/saved-hotels",
        params={"zip": "02108"},
    )

    assert populated_response.status_code == 200
    assert populated_response.json()["zip"] == "02108"
    assert populated_response.json()["count"] == 1
    assert populated_response.json()["hotels"][0]["place_id"] == (
        "provider-hotel-1"
    )
    assert [
        night["date"] for night in populated_response.json()["hotels"][0]["nights"]
    ] == FIXED_NIGHT_DATES
    assert_no_credential_fields(populated_response.text)


def test_remove_is_scoped_and_preserves_assignment_one_records(
    client: TestClient,
    database_path: Path,
) -> None:
    with closing(connect_database(database_path)) as connection:
        baseline_records = assignment_one_snapshot(connection)

    assert save_hotel(client, "02108", PROVIDER_HOTEL).status_code == 201
    assert save_hotel(client, "16802", SECOND_PROVIDER_HOTEL).status_code == 201

    response = client.delete("/api/saved-hotels/provider-hotel-1")

    assert response.status_code == 200
    assert response.json() == {"place_id": "provider-hotel-1", "deleted": True}
    assert_no_credential_fields(response.text)

    with closing(connect_database(database_path)) as connection:
        remaining_provider_ids = [
            row["provider_place_id"]
            for row in connection.execute(
                "SELECT provider_place_id FROM saved_hotels ORDER BY provider_place_id"
            )
        ]
        remaining_nights = connection.execute(
            "SELECT COUNT(*) FROM demo_hotel_nights"
        ).fetchone()[0]
        remaining_associations = connection.execute(
            "SELECT COUNT(*) FROM saved_hotel_zips"
        ).fetchone()[0]
        assignment_one_records = assignment_one_snapshot(connection)

    assert remaining_provider_ids == ["provider-hotel-2"]
    assert remaining_nights == 5
    assert remaining_associations == 1
    assert assignment_one_records == baseline_records
    assert client.get(
        "/api/saved-hotels", params={"zip": "02108"}
    ).json() == {"zip": "02108", "count": 0, "hotels": []}
    assert client.get(
        "/api/saved-hotels", params={"zip": "16802"}
    ).json()["count"] == 1


def test_lookup_rereads_committed_external_nightly_edits(
    client: TestClient,
    database_path: Path,
) -> None:
    assert save_hotel(client).status_code == 201
    first_lookup = client.get("/api/saved-hotels", params={"zip": "02108"})
    first_night = first_lookup.json()["hotels"][0]["nights"][0]
    assert first_night["nightly_rate_cents"] == 10_000
    assert first_night["rooms_available"] == 20

    with closing(connect_database(database_path)) as external_connection:
        external_connection.execute(
            """
            UPDATE demo_hotel_nights
            SET nightly_rate_cents = ?, rooms_available = ?
            WHERE night_date = ?
            """,
            (45_678, 3, "2026-10-10"),
        )
        external_connection.commit()

    second_lookup = client.get("/api/saved-hotels", params={"zip": "02108"})

    assert second_lookup.status_code == 200
    reread_night = second_lookup.json()["hotels"][0]["nights"][0]
    assert reread_night == {
        "date": "2026-10-10",
        "nightly_rate_cents": 45_678,
        "rooms_available": 3,
    }


def test_reinitializing_database_does_not_reset_existing_nightly_values(
    client: TestClient,
    database_path: Path,
) -> None:
    assert save_hotel(client).status_code == 201

    with closing(connect_database(database_path)) as connection:
        connection.execute(
            """
            UPDATE demo_hotel_nights
            SET nightly_rate_cents = ?, rooms_available = ?
            WHERE night_date = ?
            """,
            (87_654, 2, "2026-10-14"),
        )
        connection.commit()

    assert initialize_database(database_path, DATA_DIRECTORY) is False

    with closing(connect_database(database_path)) as connection:
        stored_night = connection.execute(
            """
            SELECT nightly_rate_cents, rooms_available
            FROM demo_hotel_nights
            WHERE night_date = ?
            """,
            ("2026-10-14",),
        ).fetchone()
        assert connection.execute(
            "SELECT COUNT(*) FROM demo_hotel_nights"
        ).fetchone()[0] == 5

    assert tuple(stored_night) == (87_654, 2)


def test_lookup_database_failure_is_not_reported_as_empty_success(
    client: TestClient,
    database_path: Path,
) -> None:
    with closing(connect_database(database_path)) as connection:
        connection.execute("DROP TABLE saved_hotel_zips")
        connection.commit()

    response = client.get("/api/saved-hotels", params={"zip": "02108"})

    assert response.status_code == 500
    assert response.json()["detail"]
    assert response.json() != {"zip": "02108", "count": 0, "hotels": []}
    assert "saved_hotel_zips" not in response.text
    assert_no_credential_fields(response.text)


def test_save_rolls_back_all_related_rows_when_a_night_insert_fails(
    client: TestClient,
    database_path: Path,
) -> None:
    with closing(connect_database(database_path)) as connection:
        connection.execute(
            """
            CREATE TRIGGER reject_demo_night
            BEFORE INSERT ON demo_hotel_nights
            BEGIN
                SELECT RAISE(ABORT, 'blocked test insert');
            END
            """
        )
        connection.commit()

    response = save_hotel(client)

    assert response.status_code == 500
    assert response.json() == {"detail": "Saved hotel save failed."}
    assert "blocked test insert" not in response.text
    with closing(connect_database(database_path)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM saved_hotels"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM saved_hotel_zips"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM demo_hotel_nights"
        ).fetchone()[0] == 0


def test_invalid_lookup_and_unknown_remove_return_clear_errors(
    client: TestClient,
) -> None:
    invalid_lookup = client.get("/api/saved-hotels", params={"zip": "2108"})
    missing_remove = client.delete("/api/saved-hotels/not-saved")

    assert invalid_lookup.status_code == 400
    assert invalid_lookup.json() == {
        "detail": "Enter a five-digit U.S. ZIP code."
    }
    assert missing_remove.status_code == 404
    assert missing_remove.json() == {"detail": "Saved hotel was not found."}


def test_saved_hotel_routes_never_return_credential_fields(
    client: TestClient,
) -> None:
    save_response = save_hotel(client)
    lookup_response = client.get("/api/saved-hotels", params={"zip": "02108"})
    delete_response = client.delete("/api/saved-hotels/provider-hotel-1")

    assert save_response.status_code == 201
    assert lookup_response.status_code == 200
    assert delete_response.status_code == 200
    for response in (save_response, lookup_response, delete_response):
        assert_no_credential_fields(response.text)
