import pytest
from fastapi.testclient import TestClient

from app import hotel_search, main
from app.geocoding import (
    GeoapifyHTTPError,
    GeoapifyNetworkError,
    GeoapifyNotConfiguredError,
    GeoapifyResponseError,
    GeoapifyTimeoutError,
    InvalidPostcodeError,
)


TEST_API_KEY = "hotel-route-test-key-never-return"


def test_service_uses_confirmed_zip_coordinate_as_places_center(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_centers: list[tuple[float, float]] = []
    monkeypatch.setattr(
        hotel_search,
        "lookup_us_postcode",
        lambda postcode: {
            "postcode": postcode,
            "country_code": "us",
            "latitude": 42.357,
            "longitude": -71.0637,
            "locality": "Boston",
        },
    )

    def fake_places(latitude: float, longitude: float) -> list[dict[str, object]]:
        requested_centers.append((latitude, longitude))
        return [
            {
                "place_id": "hotel-1",
                "name": "Provider Hotel",
                "latitude": 42.358,
                "longitude": -71.061,
            }
        ]

    monkeypatch.setattr(hotel_search, "search_hotels_near", fake_places)

    result = hotel_search.search_hotels_by_postcode("02108")

    assert result is not None
    assert result["search_center"]["postcode"] == "02108"
    assert result["radius_meters"] == 5_000
    assert requested_centers == [(42.357, -71.0637)]


def test_live_hotel_route_preserves_leading_zero_and_returns_provider_fields(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_postcodes: list[str] = []

    def fake_search(postcode: str) -> dict[str, object]:
        requested_postcodes.append(postcode)
        return {
            "search_center": {
                "postcode": "02108",
                "country_code": "us",
                "latitude": 42.357,
                "longitude": -71.0637,
                "locality": "Boston",
            },
            "radius_meters": 5_000,
            "hotels": [
                {
                    "place_id": "hotel-1",
                    "name": "Provider Hotel",
                    "latitude": 42.358,
                    "longitude": -71.061,
                    "formatted_address": "1 Provider Way, Boston, MA 02108",
                    "distance_meters": 321.5,
                }
            ],
        }

    monkeypatch.setattr(main, "search_hotels_by_postcode", fake_search)

    response = client.get("/api/hotels", params={"zip": "02108"})

    assert response.status_code == 200
    assert response.json() == {
        "search_center": {
            "postcode": "02108",
            "country_code": "us",
            "latitude": 42.357,
            "longitude": -71.0637,
            "locality": "Boston",
        },
        "radius_meters": 5_000,
        "count": 1,
        "hotels": [
            {
                "place_id": "hotel-1",
                "name": "Provider Hotel",
                "latitude": 42.358,
                "longitude": -71.061,
                "formatted_address": "1 Provider Way, Boston, MA 02108",
                "distance_meters": 321.5,
            }
        ],
    }
    assert requested_postcodes == ["02108"]
    assert TEST_API_KEY not in response.text


def test_live_hotel_route_returns_distinct_zero_result_response(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        main,
        "search_hotels_by_postcode",
        lambda postcode: {
            "search_center": {
                "postcode": postcode,
                "country_code": "us",
                "latitude": 40.0,
                "longitude": -75.0,
            },
            "radius_meters": 5_000,
            "hotels": [],
        },
    )

    response = client.get("/api/hotels", params={"zip": "16802"})

    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["hotels"] == []


def test_live_hotel_route_maps_invalid_and_unresolved_zip(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_invalid(_: str) -> None:
        raise InvalidPostcodeError

    monkeypatch.setattr(main, "search_hotels_by_postcode", raise_invalid)
    invalid = client.get("/api/hotels", params={"zip": "2108"})
    assert invalid.status_code == 400
    assert invalid.json() == {"detail": "Enter a five-digit U.S. ZIP code."}

    monkeypatch.setattr(main, "search_hotels_by_postcode", lambda _: None)
    unresolved = client.get("/api/hotels", params={"zip": "99999"})
    assert unresolved.status_code == 404
    assert unresolved.json() == {
        "detail": "ZIP code 99999 could not be resolved."
    }


@pytest.mark.parametrize(
    ("service_error", "expected_status", "expected_detail"),
    [
        (
            GeoapifyNotConfiguredError,
            503,
            "Geoapify service is not configured.",
        ),
        (
            GeoapifyTimeoutError,
            504,
            "Geoapify hotel search timed out.",
        ),
        (
            GeoapifyNetworkError,
            502,
            "Geoapify hotel search failed.",
        ),
        (
            GeoapifyHTTPError,
            502,
            "Geoapify hotel search failed.",
        ),
        (
            GeoapifyResponseError,
            502,
            "Geoapify hotel search failed.",
        ),
    ],
)
def test_live_hotel_route_maps_safe_service_errors(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    service_error: type[RuntimeError],
    expected_status: int,
    expected_detail: str,
) -> None:
    def raise_service_error(_: str) -> None:
        raise service_error(TEST_API_KEY)

    monkeypatch.setattr(main, "search_hotels_by_postcode", raise_service_error)

    response = client.get("/api/hotels", params={"zip": "02108"})

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
    assert TEST_API_KEY not in response.text
