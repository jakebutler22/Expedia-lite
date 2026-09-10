from fastapi.testclient import TestClient

from app.main import app
from app.search import search_stays


client = TestClient(app)


def test_boston_search_joins_hotels_and_trips() -> None:
    stays = search_stays("Boston")

    assert [stay.trip_id for stay in stays] == ["T001", "T002", "T009", "T010"]
    assert stays[0].hotel_name == "Harbor Lantern Hotel"
    assert stays[0].nights == 2
    assert stays[0].stay_price_usd == 300


def test_search_is_case_insensitive_and_trims_spaces() -> None:
    assert len(search_stays("  bOsToN  ")) == 4


def test_unknown_city_returns_no_stays() -> None:
    assert search_stays("Miami") == []


def test_api_returns_search_metadata_and_stays() -> None:
    response = client.get("/api/stays", params={"city": "New York"})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "New York"
    assert body["count"] == 3
    assert [stay["trip_id"] for stay in body["stays"]] == ["T003", "T004", "T011"]


def test_api_rejects_blank_city() -> None:
    response = client.get("/api/stays", params={"city": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Enter a city to search."
