import csv
from datetime import date
from pathlib import Path

from .models import Stay


DATA_DIRECTORY = Path(__file__).resolve().parent.parent / "data"
HOTELS_FILE = DATA_DIRECTORY / "hotels.csv"
TRIPS_FILE = DATA_DIRECTORY / "trips.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read an instructor-supplied UTF-8 CSV, including files with a BOM."""

    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def search_stays(city: str) -> list[Stay]:
    """Return trips whose joined hotel city equals the normalized query."""

    normalized_city = city.strip().casefold()
    if not normalized_city:
        return []

    hotels_by_id = {
        hotel["hotel_id"]: hotel
        for hotel in _read_csv(HOTELS_FILE)
        if hotel["city"].strip().casefold() == normalized_city
    }

    stays: list[Stay] = []
    for trip in _read_csv(TRIPS_FILE):
        hotel = hotels_by_id.get(trip["hotel_id"])
        if hotel is None:
            continue

        check_in = date.fromisoformat(trip["check_in"])
        check_out = date.fromisoformat(trip["check_out"])
        nights = (check_out - check_in).days
        nightly_rate = float(hotel["nightly_rate_usd"])

        stays.append(
            Stay(
                trip_id=trip["trip_id"],
                trip_name=trip["trip_name"],
                hotel_id=hotel["hotel_id"],
                hotel_name=hotel["hotel_name"],
                city=hotel["city"],
                state=hotel["state"],
                check_in=trip["check_in"],
                check_out=trip["check_out"],
                nights=nights,
                nightly_rate_usd=nightly_rate,
                stay_price_usd=nightly_rate * nights,
            )
        )

    return stays
