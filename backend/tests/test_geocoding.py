import httpx
import pytest

from app import geocoding


TEST_API_KEY = "test-api-key-never-return"


def configured_key() -> str:
    return TEST_API_KEY


def test_zip_lookup_returns_exact_us_postcode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request: dict[str, object] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, object],
        timeout: float,
    ) -> httpx.Response:
        captured_request.update(url=url, params=params, timeout=timeout)
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json={
                "results": [
                    {
                        "postcode": "02108",
                        "country_code": "us",
                        "city": "Boston",
                        "lat": 42.357,
                        "lon": -71.0637,
                    }
                ]
            },
        )

    monkeypatch.setattr(geocoding, "get_geoapify_api_key", configured_key)
    monkeypatch.setattr(geocoding.httpx, "get", fake_get)

    result = geocoding.lookup_us_postcode("02108")

    assert result == {
        "postcode": "02108",
        "country_code": "us",
        "latitude": 42.357,
        "longitude": -71.0637,
        "locality": "Boston",
    }
    assert captured_request == {
        "url": geocoding.GEOAPIFY_GEOCODING_URL,
        "params": {
            "postcode": "02108",
            "type": "postcode",
            "filter": "countrycode:us",
            "format": "json",
            "limit": 1,
            "apiKey": TEST_API_KEY,
        },
        "timeout": geocoding.GEOAPIFY_TIMEOUT_SECONDS,
    }
    assert TEST_API_KEY not in repr(result)


@pytest.mark.parametrize(
    "provider_result",
    [
        {
            "postcode": "16802",
            "country_code": "us",
            "lat": 40.79,
            "lon": -77.86,
        },
        {
            "postcode": "02108",
            "country_code": "ca",
            "lat": 40.79,
            "lon": -77.86,
        },
    ],
)
def test_zip_lookup_rejects_mismatched_location(
    monkeypatch: pytest.MonkeyPatch,
    provider_result: dict[str, object],
) -> None:
    monkeypatch.setattr(geocoding, "get_geoapify_api_key", configured_key)
    monkeypatch.setattr(
        geocoding.httpx,
        "get",
        lambda *args, **kwargs: httpx.Response(
            200,
            request=httpx.Request("GET", geocoding.GEOAPIFY_GEOCODING_URL),
            json={"results": [provider_result]},
        ),
    )

    assert geocoding.lookup_us_postcode("02108") is None


@pytest.mark.parametrize(
    "postcode",
    ["", "1680", "1680A", "168020", " 16802", "16802 "],
)
def test_zip_lookup_rejects_invalid_postcode_without_provider_request(
    monkeypatch: pytest.MonkeyPatch,
    postcode: str,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> httpx.Response:
        raise AssertionError("Geoapify should not be called for an invalid ZIP.")

    monkeypatch.setattr(geocoding.httpx, "get", fail_if_called)

    with pytest.raises(geocoding.InvalidPostcodeError):
        geocoding.lookup_us_postcode(postcode)


def test_zip_lookup_sanitizes_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(geocoding, "get_geoapify_api_key", configured_key)
    monkeypatch.setattr(
        geocoding.httpx,
        "get",
        lambda *args, **kwargs: httpx.Response(
            503,
            request=httpx.Request("GET", geocoding.GEOAPIFY_GEOCODING_URL),
            text=f"provider failure containing {TEST_API_KEY}",
        ),
    )

    with pytest.raises(geocoding.GeoapifyHTTPError) as error:
        geocoding.lookup_us_postcode("02108")

    assert TEST_API_KEY not in str(error.value)
