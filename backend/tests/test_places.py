import httpx
import pytest

from app import places


TEST_API_KEY = "places-test-key-never-return"


def configured_key() -> str:
    return TEST_API_KEY


def test_hotel_search_uses_hard_5km_filter_and_normalizes_provider_data(
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
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "place_id": "hotel-1",
                            "name": "Provider Hotel",
                            "lat": 42.358,
                            "lon": -71.061,
                            "formatted": "1 Provider Way, Boston, MA 02108",
                            "address_line1": "1 Provider Way",
                            "address_line2": "Boston, MA 02108",
                            "city": "Boston",
                            "state": "Massachusetts",
                            "postcode": "02108",
                            "country": "United States",
                            "distance": 321.5,
                            "categories": [
                                "accommodation",
                                "accommodation.hotel",
                            ],
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-71.061, 42.358],
                        },
                    },
                    {
                        "type": "Feature",
                        "properties": {
                            "place_id": "hotel-2",
                            "name": "Geometry Hotel",
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-71.06, 42.36],
                        },
                    },
                    {
                        "type": "Feature",
                        "properties": {
                            "place_id": "hotel-1",
                            "name": "Duplicate Provider Hotel",
                            "lat": 42.359,
                            "lon": -71.062,
                        },
                        "geometry": None,
                    },
                    {
                        "type": "Feature",
                        "properties": {
                            "place_id": "unnamed-place",
                            "lat": 42.357,
                            "lon": -71.063,
                        },
                        "geometry": None,
                    },
                ],
            },
        )

    monkeypatch.setattr(places, "get_geoapify_api_key", configured_key)
    monkeypatch.setattr(places.httpx, "get", fake_get)

    result = places.search_hotels_near(42.357, -71.0637)

    assert result == [
        {
            "place_id": "hotel-1",
            "name": "Provider Hotel",
            "latitude": 42.358,
            "longitude": -71.061,
            "formatted_address": "1 Provider Way, Boston, MA 02108",
            "address_line1": "1 Provider Way",
            "address_line2": "Boston, MA 02108",
            "city": "Boston",
            "state": "Massachusetts",
            "postcode": "02108",
            "country": "United States",
            "distance_meters": 321.5,
            "categories": ["accommodation", "accommodation.hotel"],
        },
        {
            "place_id": "hotel-2",
            "name": "Geometry Hotel",
            "latitude": 42.36,
            "longitude": -71.06,
        },
    ]
    assert captured_request == {
        "url": places.GEOAPIFY_PLACES_URL,
        "params": {
            "categories": "accommodation.hotel",
            "filter": "circle:-71.0637,42.357,5000",
            "bias": "proximity:-71.0637,42.357",
            "limit": 20,
            "apiKey": TEST_API_KEY,
        },
        "timeout": places.GEOAPIFY_TIMEOUT_SECONDS,
    }
    assert TEST_API_KEY not in repr(result)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"type": "FeatureCollection", "features": None},
        {"type": "FeatureCollection", "features": [None]},
        {"type": "FeatureCollection", "features": [{"properties": None}]},
    ],
)
def test_hotel_search_rejects_malformed_provider_response(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
) -> None:
    monkeypatch.setattr(places, "get_geoapify_api_key", configured_key)
    monkeypatch.setattr(
        places.httpx,
        "get",
        lambda *args, **kwargs: httpx.Response(
            200,
            request=httpx.Request("GET", places.GEOAPIFY_PLACES_URL),
            json=payload,
        ),
    )

    with pytest.raises(places.GeoapifyResponseError):
        places.search_hotels_near(42.357, -71.0637)


def test_hotel_search_sanitizes_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(places, "get_geoapify_api_key", configured_key)
    monkeypatch.setattr(
        places.httpx,
        "get",
        lambda *args, **kwargs: httpx.Response(
            503,
            request=httpx.Request("GET", places.GEOAPIFY_PLACES_URL),
            text=f"provider failure containing {TEST_API_KEY}",
        ),
    )

    with pytest.raises(places.GeoapifyHTTPError) as error:
        places.search_hotels_near(42.357, -71.0637)

    assert TEST_API_KEY not in str(error.value)
