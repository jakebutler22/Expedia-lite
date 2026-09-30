import math
from typing import NotRequired, TypedDict

import httpx

from .config import get_geoapify_api_key
from .geocoding import (
    GeoapifyHTTPError,
    GeoapifyNetworkError,
    GeoapifyNotConfiguredError,
    GeoapifyResponseError,
    GeoapifyTimeoutError,
)


GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"
GEOAPIFY_TIMEOUT_SECONDS = 5.0
HOTEL_CATEGORY = "accommodation.hotel"
HOTEL_SEARCH_RADIUS_METERS = 5_000
HOTEL_SEARCH_LIMIT = 20


class HotelResult(TypedDict):
    place_id: str
    name: str
    latitude: float
    longitude: float
    formatted_address: NotRequired[str]
    address_line1: NotRequired[str]
    address_line2: NotRequired[str]
    city: NotRequired[str]
    state: NotRequired[str]
    postcode: NotRequired[str]
    country: NotRequired[str]
    distance_meters: NotRequired[float]
    categories: NotRequired[list[str]]


def _text(properties: dict[str, object], field: str) -> str | None:
    value = properties.get(field)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _number_in_range(
    value: object,
    minimum: float,
    maximum: float,
) -> float | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    normalized = float(value)
    if not math.isfinite(normalized) or not minimum <= normalized <= maximum:
        return None
    return normalized


def _feature_coordinates(
    feature: dict[str, object],
    properties: dict[str, object],
) -> tuple[float, float] | None:
    latitude = _number_in_range(properties.get("lat"), -90, 90)
    longitude = _number_in_range(properties.get("lon"), -180, 180)
    if latitude is not None and longitude is not None:
        return latitude, longitude

    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        return None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None

    longitude = _number_in_range(coordinates[0], -180, 180)
    latitude = _number_in_range(coordinates[1], -90, 90)
    if latitude is None or longitude is None:
        return None
    return latitude, longitude


def _normalize_hotels(payload: object) -> list[HotelResult]:
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise GeoapifyResponseError

    features = payload.get("features")
    if not isinstance(features, list):
        raise GeoapifyResponseError

    hotels: list[HotelResult] = []
    seen_place_ids: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            raise GeoapifyResponseError
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise GeoapifyResponseError

        place_id = _text(properties, "place_id")
        name = _text(properties, "name")
        coordinates = _feature_coordinates(feature, properties)
        if place_id is None or name is None or coordinates is None:
            continue
        if place_id in seen_place_ids:
            continue

        latitude, longitude = coordinates
        hotel: HotelResult = {
            "place_id": place_id,
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
        }

        for provider_field, response_field in (
            ("formatted", "formatted_address"),
            ("address_line1", "address_line1"),
            ("address_line2", "address_line2"),
            ("city", "city"),
            ("state", "state"),
            ("postcode", "postcode"),
            ("country", "country"),
        ):
            value = _text(properties, provider_field)
            if value is not None:
                hotel[response_field] = value  # type: ignore[literal-required]

        distance = properties.get("distance")
        if (
            isinstance(distance, (int, float))
            and not isinstance(distance, bool)
            and math.isfinite(float(distance))
            and float(distance) >= 0
        ):
            hotel["distance_meters"] = float(distance)

        categories = properties.get("categories")
        if isinstance(categories, list):
            normalized_categories = [
                value.strip()
                for value in categories
                if isinstance(value, str) and value.strip()
            ]
            if normalized_categories:
                hotel["categories"] = normalized_categories

        seen_place_ids.add(place_id)
        hotels.append(hotel)

    return hotels


def search_hotels_near(latitude: float, longitude: float) -> list[HotelResult]:
    """Return displayable Geoapify hotel places within 5 km of a point."""
    normalized_latitude = _number_in_range(latitude, -90, 90)
    normalized_longitude = _number_in_range(longitude, -180, 180)
    if normalized_latitude is None or normalized_longitude is None:
        raise GeoapifyResponseError

    api_key = get_geoapify_api_key()
    if api_key is None:
        raise GeoapifyNotConfiguredError

    center = f"{normalized_longitude},{normalized_latitude}"
    try:
        response = httpx.get(
            GEOAPIFY_PLACES_URL,
            params={
                "categories": HOTEL_CATEGORY,
                "filter": f"circle:{center},{HOTEL_SEARCH_RADIUS_METERS}",
                "bias": f"proximity:{center}",
                "limit": HOTEL_SEARCH_LIMIT,
                "apiKey": api_key,
            },
            timeout=GEOAPIFY_TIMEOUT_SECONDS,
        )
    except httpx.TimeoutException:
        raise GeoapifyTimeoutError from None
    except httpx.RequestError:
        raise GeoapifyNetworkError from None

    if not response.is_success:
        raise GeoapifyHTTPError

    try:
        payload = response.json()
    except ValueError:
        raise GeoapifyResponseError from None

    return _normalize_hotels(payload)
