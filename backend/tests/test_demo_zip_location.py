import httpx
import pytest
from fastapi.testclient import TestClient

from app import geocoding, main
from app.geocoding import (
    GeoapifyHTTPError,
    GeoapifyNetworkError,
    GeoapifyNotConfiguredError,
    GeoapifyResponseError,
    GeoapifyTimeoutError,
)


TEST_API_KEY = "route-test-key-never-return"


def test_demo_zip_location_always_uses_16802(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_postcodes: list[str] = []

    def fake_lookup(postcode: str) -> dict[str, object]:
        requested_postcodes.append(postcode)
        return {
            "postcode": "16802",
            "country_code": "us",
            "latitude": 40.7982,
            "longitude": -77.8599,
            "locality": "University Park",
        }

    monkeypatch.setattr(main, "lookup_us_postcode", fake_lookup)

    response = client.get(
        "/api/demo/zip-location",
        params={"zip": "02108"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "postcode": "16802",
        "country_code": "us",
        "latitude": 40.7982,
        "longitude": -77.8599,
        "locality": "University Park",
    }
    assert requested_postcodes == ["16802"]
    assert TEST_API_KEY not in response.text


def test_dynamic_zip_location_preserves_leading_zero_and_uses_controller(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_postcodes: list[str] = []

    def fake_lookup(postcode: str) -> dict[str, object]:
        requested_postcodes.append(postcode)
        return {
            "postcode": "02108",
            "country_code": "us",
            "latitude": 42.357,
            "longitude": -71.0637,
            "locality": "Boston",
        }

    monkeypatch.setattr(main, "lookup_us_postcode", fake_lookup)

    response = client.get(
        "/api/zip-location",
        params={"zip": "02108"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "postcode": "02108",
        "country_code": "us",
        "latitude": 42.357,
        "longitude": -71.0637,
        "locality": "Boston",
    }
    assert requested_postcodes == ["02108"]
    assert TEST_API_KEY not in response.text


@pytest.mark.parametrize(
    "postcode",
    ["1680", "168021", "16A02", "", "   ", " 16802", "16802 "],
)
def test_dynamic_zip_location_rejects_invalid_format_without_provider_request(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    postcode: str,
) -> None:
    def fail_if_key_is_read() -> str:
        raise AssertionError("Configuration should not be read for an invalid ZIP.")

    def fail_if_called(*args: object, **kwargs: object) -> httpx.Response:
        raise AssertionError("Geoapify should not be called for an invalid ZIP.")

    monkeypatch.setattr(geocoding, "get_geoapify_api_key", fail_if_key_is_read)
    monkeypatch.setattr(geocoding.httpx, "get", fail_if_called)

    response = client.get(
        "/api/zip-location",
        params={"zip": postcode},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Enter a five-digit U.S. ZIP code."}
    assert TEST_API_KEY not in response.text


def test_dynamic_zip_location_requires_zip_parameter(client: TestClient) -> None:
    response = client.get("/api/zip-location")

    assert response.status_code == 422
    assert TEST_API_KEY not in response.text


def test_dynamic_zip_location_maps_missing_configuration(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_not_configured(_: str) -> None:
        raise GeoapifyNotConfiguredError(TEST_API_KEY)

    monkeypatch.setattr(main, "lookup_us_postcode", raise_not_configured)

    response = client.get(
        "/api/zip-location",
        params={"zip": "16802"},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Geoapify service is not configured."}
    assert TEST_API_KEY not in response.text


def test_dynamic_zip_location_maps_unresolved_zip(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main, "lookup_us_postcode", lambda _: None)

    response = client.get(
        "/api/zip-location",
        params={"zip": "99999"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "ZIP code 99999 could not be resolved."
    }
    assert TEST_API_KEY not in response.text


@pytest.mark.parametrize(
    ("controller_error", "expected_status", "expected_detail"),
    [
        (
            GeoapifyTimeoutError,
            504,
            "Geoapify ZIP lookup timed out.",
        ),
        (
            GeoapifyNetworkError,
            502,
            "Geoapify ZIP lookup failed.",
        ),
        (
            GeoapifyHTTPError,
            502,
            "Geoapify ZIP lookup failed.",
        ),
        (
            GeoapifyResponseError,
            502,
            "Geoapify ZIP lookup failed.",
        ),
    ],
)
def test_dynamic_zip_location_maps_provider_failure(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    controller_error: type[RuntimeError],
    expected_status: int,
    expected_detail: str,
) -> None:
    def raise_provider_error(_: str) -> None:
        raise controller_error(TEST_API_KEY)

    monkeypatch.setattr(main, "lookup_us_postcode", raise_provider_error)

    response = client.get(
        "/api/zip-location",
        params={"zip": "16802"},
    )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
    assert TEST_API_KEY not in response.text
