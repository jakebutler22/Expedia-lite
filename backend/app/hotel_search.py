from typing import TypedDict

from .geocoding import ZipLocationResult, lookup_us_postcode
from .places import HOTEL_SEARCH_RADIUS_METERS, HotelResult, search_hotels_near


class LiveHotelSearchResult(TypedDict):
    search_center: ZipLocationResult
    radius_meters: int
    hotels: list[HotelResult]


def search_hotels_by_postcode(postcode: str) -> LiveHotelSearchResult | None:
    """Resolve an exact U.S. ZIP and search hotels around its coordinates."""
    search_center = lookup_us_postcode(postcode)
    if search_center is None:
        return None

    hotels = search_hotels_near(
        search_center["latitude"],
        search_center["longitude"],
    )
    return {
        "search_center": search_center,
        "radius_meters": HOTEL_SEARCH_RADIUS_METERS,
        "hotels": hotels,
    }
