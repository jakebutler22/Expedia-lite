from datetime import date

import pytest
from fastapi.testclient import TestClient


def test_users_are_read_from_seeded_database(client: TestClient) -> None:
    response = client.get("/api/users")

    assert response.status_code == 200
    assert [user["user_id"] for user in response.json()] == [
        "U001",
        "U002",
        "U003",
        "U004",
        "U005",
        "U006",
    ]


def test_supplied_traveler_can_have_empty_booking_history(client: TestClient) -> None:
    response = client.get("/api/users/U006/bookings")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "U006",
        "display_name": "Demo Traveler 6",
        "count": 0,
        "bookings": [],
    }


def test_booking_lifecycle_and_ids_are_persistent_and_not_reused(
    client: TestClient,
) -> None:
    search_response = client.get("/api/stays", params={"city": "Harbor"})
    assert search_response.status_code == 200
    assert [stay["trip_id"] for stay in search_response.json()["stays"]] == [
        "T001",
        "T009",
    ]

    create_response = client.post(
        "/api/bookings",
        json={"user_id": "U006", "trip_id": "T001"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["booking_id"] == "B007"
    assert created["user_id"] == "U006"
    assert created["status"] == "confirmed"
    assert created["stay"]["trip_id"] == "T001"
    date.fromisoformat(created["booked_on"])

    get_response = client.get("/api/bookings/B007")
    assert get_response.status_code == 200
    assert get_response.json() == created

    history_response = client.get("/api/users/U006/bookings")
    assert history_response.status_code == 200
    assert history_response.json()["count"] == 1
    assert history_response.json()["bookings"] == [created]

    cancel_response = client.patch("/api/bookings/B007/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    cancelled_history = client.get("/api/users/U006/bookings").json()
    assert cancelled_history["count"] == 1
    assert cancelled_history["bookings"][0]["booking_id"] == "B007"
    assert cancelled_history["bookings"][0]["status"] == "cancelled"

    delete_response = client.delete("/api/bookings/B007")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"booking_id": "B007", "deleted": True}

    empty_history = client.get("/api/users/U006/bookings").json()
    assert empty_history["count"] == 0
    assert empty_history["bookings"] == []

    deleted_response = client.get("/api/bookings/B007")
    assert deleted_response.status_code == 404
    assert deleted_response.json() == {"detail": "Booking B007 was not found."}

    second_create_response = client.post(
        "/api/bookings",
        json={"user_id": "U006", "trip_id": "T002"},
    )
    assert second_create_response.status_code == 201
    assert second_create_response.json()["booking_id"] == "B008"


def test_unknown_user_and_trip_return_not_found(client: TestClient) -> None:
    history_response = client.get("/api/users/U999/bookings")
    assert history_response.status_code == 404
    assert history_response.json() == {"detail": "Traveler U999 was not found."}

    user_response = client.post(
        "/api/bookings",
        json={"user_id": "U999", "trip_id": "T001"},
    )
    assert user_response.status_code == 404
    assert user_response.json() == {"detail": "Traveler U999 was not found."}

    trip_response = client.post(
        "/api/bookings",
        json={"user_id": "U001", "trip_id": "T999"},
    )
    assert trip_response.status_code == 404
    assert trip_response.json() == {"detail": "Trip T999 was not found."}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/bookings/B999"),
        ("patch", "/api/bookings/B999/cancel"),
        ("delete", "/api/bookings/B999"),
    ],
)
def test_unknown_booking_returns_not_found(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    response = client.request(method, path)

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking B999 was not found."}


@pytest.mark.parametrize(
    "payload",
    [
        {"user_id": "U001"},
        {"user_id": "   ", "trip_id": "T001"},
        ["U001", "T001"],
    ],
)
def test_malformed_booking_request_returns_validation_error(
    client: TestClient,
    payload: object,
) -> None:
    response = client.post("/api/bookings", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]
