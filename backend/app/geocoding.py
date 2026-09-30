import math
import re
from typing import NotRequired, TypedDict

import httpx

from .config import get_geoapify_api_key


GEOAPIFY_GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"
GEOAPIFY_TIMEOUT_SECONDS = 5.0
US_POSTCODE_PATTERN = re.compile(r"[0-9]{5}")


class ZipLocationResult(TypedDict):
    postcode: str
    country_code: str
    latitude: float
    longitude: float
    locality: NotRequired[str]


class GeoapifyNotConfiguredError(RuntimeError):
    pass


class GeoapifyTimeoutError(RuntimeError):
    pass


class GeoapifyNetworkError(RuntimeError):
    pass


class GeoapifyHTTPError(RuntimeError):
    pass


class GeoapifyResponseError(RuntimeError):
    pass


class InvalidPostcodeError(ValueError):
    pass


def _normalize_zip_result(
    payload: object,
    requested_postcode: str,
) -> ZipLocationResult | None:
    if not isinstance(payload, dict):
        raise GeoapifyResponseError

    results = payload.get("results")
    if not isinstance(results, list):
        raise GeoapifyResponseError

    for result in results:
        if not isinstance(result, dict):
            raise GeoapifyResponseError

        postcode = result.get("postcode")
        country_code = result.get("country_code")
        if (
            not isinstance(postcode, str)
            or postcode.strip() != requested_postcode
            or not isinstance(country_code, str)
            or country_code.strip().lower() != "us"
        ):
            continue

        latitude = result.get("lat")
        longitude = result.get("lon")
        coordinates_are_numbers = (
            isinstance(latitude, (int, float))
            and not isinstance(latitude, bool)
            and isinstance(longitude, (int, float))
            and not isinstance(longitude, bool)
        )
        if not coordinates_are_numbers:
            raise GeoapifyResponseError

        normalized_latitude = float(latitude)
        normalized_longitude = float(longitude)
        if (
            not math.isfinite(normalized_latitude)
            or not math.isfinite(normalized_longitude)
            or not -90 <= normalized_latitude <= 90
            or not -180 <= normalized_longitude <= 180
        ):
            raise GeoapifyResponseError

        location: ZipLocationResult = {
            "postcode": requested_postcode,
            "country_code": "us",
            "latitude": normalized_latitude,
            "longitude": normalized_longitude,
        }
        for locality_field in ("city", "town", "village", "municipality"):
            locality = result.get(locality_field)
            if isinstance(locality, str) and locality.strip():
                location["locality"] = locality.strip()
                break

        return location

    return None


def lookup_us_postcode(postcode: str) -> ZipLocationResult | None:
    """Resolve an exact U.S. postcode, or return None when it is unresolved.

    Provider configuration, transport, HTTP, and malformed-response failures
    raise the sanitized Geoapify error types declared in this module.
    """
    normalized_postcode = postcode
    if US_POSTCODE_PATTERN.fullmatch(normalized_postcode) is None:
        raise InvalidPostcodeError

    api_key = get_geoapify_api_key()
    if api_key is None:
        raise GeoapifyNotConfiguredError

    try:
        response = httpx.get(
            GEOAPIFY_GEOCODING_URL,
            params={
                "postcode": normalized_postcode,
                "type": "postcode",
                "filter": "countrycode:us",
                "format": "json",
                "limit": 1,
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

    return _normalize_zip_result(payload, normalized_postcode)
