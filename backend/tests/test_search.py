import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.search import search_stays


def test_boston_search_joins_hotels_and_trips(
    connection: sqlite3.Connection,
) -> None:
    stays = search_stays(connection, "Boston")

    assert [stay["trip_id"] for stay in stays] == ["T001", "T002", "T009", "T010"]
    assert stays[0]["hotel_name"] == "Harbor Lantern Hotel"
    assert stays[0]["nights"] == 2
    assert stays[0]["stay_price_usd"] == 300


def test_city_search_is_case_insensitive_and_trims_spaces(
    connection: sqlite3.Connection,
) -> None:
    stays = search_stays(connection, "  bOsToN  ")

    assert [stay["trip_id"] for stay in stays] == ["T001", "T002", "T009", "T010"]


@pytest.mark.parametrize(
    ("query", "expected_trip_ids"),
    [
        ("Harbor Lantern Hotel", ["T001", "T009"]),
        ("  hArBoR  ", ["T001", "T009"]),
        ("Miami", []),
    ],
)
def test_hotel_name_and_no_match_searches(
    connection: sqlite3.Connection,
    query: str,
    expected_trip_ids: list[str],
) -> None:
    stays = search_stays(connection, query)

    assert [stay["trip_id"] for stay in stays] == expected_trip_ids


def test_api_returns_search_metadata_and_stays(client: TestClient) -> None:
    response = client.get("/api/stays", params={"query": "New York"})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "New York"
    assert body["count"] == 3
    assert [stay["trip_id"] for stay in body["stays"]] == ["T003", "T004", "T011"]


@pytest.mark.parametrize("parameter_name", ["query", "city"])
def test_api_accepts_preferred_query_and_deprecated_city_alias(
    client: TestClient,
    parameter_name: str,
) -> None:
    response = client.get("/api/stays", params={parameter_name: "Harbor"})

    assert response.status_code == 200
    assert [stay["trip_id"] for stay in response.json()["stays"]] == [
        "T001",
        "T009",
    ]


def test_openapi_describes_search_parameters(client: TestClient) -> None:
    parameters = client.get("/openapi.json").json()["paths"]["/api/stays"]["get"][
        "parameters"
    ]
    parameters_by_name = {parameter["name"]: parameter for parameter in parameters}

    assert parameters_by_name["query"]["description"] == (
        "Hotel name or city, matched case-insensitively"
    )
    assert parameters_by_name["city"]["deprecated"] is True


def test_api_rejects_blank_search_query(client: TestClient) -> None:
    response = client.get("/api/stays", params={"city": "   "})

    assert response.status_code == 400
    assert response.json() == {"detail": "Enter a hotel name or city to search."}
