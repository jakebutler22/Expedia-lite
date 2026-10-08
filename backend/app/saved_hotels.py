import math
import re
import sqlite3
from collections.abc import Mapping


ZIP_PATTERN = re.compile(r"[0-9]{5}")
DEMO_NIGHT_DATES = (
    "2026-10-10",
    "2026-10-11",
    "2026-10-12",
    "2026-10-13",
    "2026-10-14",
)


class InvalidSavedHotelRequestError(ValueError):
    pass


class SavedHotelNotFoundError(LookupError):
    pass


def _normalize_zip(searched_zip: str) -> str:
    normalized_zip = searched_zip.strip()
    if ZIP_PATTERN.fullmatch(normalized_zip) is None:
        raise InvalidSavedHotelRequestError(
            "Enter a five-digit U.S. ZIP code."
        )
    return normalized_zip


def _required_text(hotel: Mapping[str, object], field: str) -> str:
    value = hotel.get(field)
    if not isinstance(value, str) or not value.strip():
        raise InvalidSavedHotelRequestError(
            f"Hotel {field.replace('_', ' ')} is required."
        )
    return value.strip()


def _optional_text(hotel: Mapping[str, object], field: str) -> str | None:
    value = hotel.get(field)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _coordinate(
    hotel: Mapping[str, object],
    field: str,
    minimum: float,
    maximum: float,
) -> float:
    value = hotel.get(field)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise InvalidSavedHotelRequestError(
            f"Hotel {field} must be a valid coordinate."
        )
    normalized = float(value)
    if not math.isfinite(normalized) or not minimum <= normalized <= maximum:
        raise InvalidSavedHotelRequestError(
            f"Hotel {field} must be a valid coordinate."
        )
    return normalized


def _hotel_address(hotel: Mapping[str, object]) -> str:
    address = _optional_text(hotel, "address")
    if address is not None:
        return address

    formatted = _optional_text(hotel, "formatted_address")
    if formatted is not None:
        return formatted

    street_parts = [
        value
        for field in ("address_line1", "address_line2")
        if (value := _optional_text(hotel, field)) is not None
    ]
    if street_parts:
        return ", ".join(street_parts)

    locality_parts = [
        value
        for field in ("city", "state", "postcode", "country")
        if (value := _optional_text(hotel, field)) is not None
    ]
    if locality_parts:
        return ", ".join(locality_parts)

    raise InvalidSavedHotelRequestError("Hotel address is required.")


def _saved_hotel_record(
    connection: sqlite3.Connection,
    row: sqlite3.Row,
) -> dict[str, object]:
    searched_zips = [
        association["searched_zip"]
        for association in connection.execute(
            """
            SELECT searched_zip
            FROM saved_hotel_zips
            WHERE saved_hotel_id = ?
            ORDER BY searched_zip
            """,
            (row["saved_hotel_id"],),
        ).fetchall()
    ]
    nights = [
        {
            "date": night["night_date"],
            "nightly_rate_cents": night["nightly_rate_cents"],
            "rooms_available": night["rooms_available"],
        }
        for night in connection.execute(
            """
            SELECT night_date, nightly_rate_cents, rooms_available
            FROM demo_hotel_nights
            WHERE saved_hotel_id = ?
            ORDER BY night_date
            """,
            (row["saved_hotel_id"],),
        ).fetchall()
    ]
    return {
        "place_id": row["provider_place_id"],
        "name": row["hotel_name"],
        "address": row["address"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "searched_zips": searched_zips,
        "nights": nights,
    }


def list_saved_hotels_by_zip(
    connection: sqlite3.Connection,
    searched_zip: str,
) -> list[dict[str, object]]:
    """Read the current committed saved hotels and nights for a searched ZIP."""

    normalized_zip = _normalize_zip(searched_zip)
    rows = connection.execute(
        """
        SELECT
            saved_hotels.saved_hotel_id,
            saved_hotels.provider_place_id,
            saved_hotels.hotel_name,
            saved_hotels.address,
            saved_hotels.latitude,
            saved_hotels.longitude
        FROM saved_hotels
        JOIN saved_hotel_zips
          ON saved_hotel_zips.saved_hotel_id =
             saved_hotels.saved_hotel_id
        WHERE saved_hotel_zips.searched_zip = ?
        ORDER BY saved_hotels.hotel_name COLLATE NOCASE,
                 saved_hotels.provider_place_id
        """,
        (normalized_zip,),
    ).fetchall()
    return [_saved_hotel_record(connection, row) for row in rows]


def save_provider_hotel(
    connection: sqlite3.Connection,
    searched_zip: str,
    hotel: Mapping[str, object],
) -> dict[str, object]:
    """Atomically save one provider hotel, its ZIP, and fixed demo nights."""

    normalized_zip = _normalize_zip(searched_zip)
    place_id = _required_text(hotel, "place_id")
    name = _required_text(hotel, "name")
    address = _hotel_address(hotel)
    latitude = _coordinate(hotel, "latitude", -90, 90)
    longitude = _coordinate(hotel, "longitude", -180, 180)

    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            INSERT INTO saved_hotels (
                provider_place_id,
                hotel_name,
                address,
                latitude,
                longitude
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (provider_place_id) DO NOTHING
            """,
            (place_id, name, address, latitude, longitude),
        )
        saved_hotel = connection.execute(
            """
            SELECT saved_hotel_id
            FROM saved_hotels
            WHERE provider_place_id = ?
            """,
            (place_id,),
        ).fetchone()
        if saved_hotel is None:
            raise RuntimeError("Saved hotel could not be read after insertion.")

        saved_hotel_id = saved_hotel["saved_hotel_id"]
        connection.execute(
            """
            INSERT INTO saved_hotel_zips (
                saved_hotel_id,
                searched_zip
            ) VALUES (?, ?)
            ON CONFLICT (saved_hotel_id, searched_zip) DO NOTHING
            """,
            (saved_hotel_id, normalized_zip),
        )
        connection.executemany(
            """
            INSERT INTO demo_hotel_nights (saved_hotel_id, night_date)
            VALUES (?, ?)
            ON CONFLICT (saved_hotel_id, night_date) DO NOTHING
            """,
            [(saved_hotel_id, night_date) for night_date in DEMO_NIGHT_DATES],
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    row = connection.execute(
        """
        SELECT
            saved_hotel_id,
            provider_place_id,
            hotel_name,
            address,
            latitude,
            longitude
        FROM saved_hotels
        WHERE provider_place_id = ?
        """,
        (place_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("Saved hotel could not be read after commit.")
    return _saved_hotel_record(connection, row)


def remove_saved_hotel(
    connection: sqlite3.Connection,
    place_id: str,
) -> str:
    """Delete one saved provider hotel and cascade only its local children."""

    normalized_place_id = place_id.strip()
    if not normalized_place_id:
        raise InvalidSavedHotelRequestError("Hotel place ID is required.")

    try:
        connection.execute("BEGIN IMMEDIATE")
        result = connection.execute(
            "DELETE FROM saved_hotels WHERE provider_place_id = ?",
            (normalized_place_id,),
        )
        if result.rowcount == 0:
            raise SavedHotelNotFoundError("Saved hotel was not found.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    return normalized_place_id
