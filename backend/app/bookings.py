import sqlite3
from datetime import date

from .domain import build_stay_record, format_booking_id


class InvalidBookingRequestError(ValueError):
    pass


class UserNotFoundError(LookupError):
    pass


class TripNotFoundError(LookupError):
    pass


class BookingNotFoundError(LookupError):
    pass


BOOKING_SELECT = """
    SELECT
        bookings.booking_id,
        bookings.user_id,
        bookings.trip_id,
        bookings.booked_on,
        bookings.status,
        users.display_name,
        trips.trip_name,
        trips.check_in,
        trips.check_out,
        hotels.hotel_id,
        hotels.hotel_name,
        hotels.city,
        hotels.state,
        hotels.nightly_rate_usd
    FROM bookings
    JOIN users ON users.user_id = bookings.user_id
    JOIN trips ON trips.trip_id = bookings.trip_id
    JOIN hotels ON hotels.hotel_id = trips.hotel_id
"""


def _booking_record(row: sqlite3.Row) -> dict[str, object]:
    stay = build_stay_record(
        trip_id=row["trip_id"],
        trip_name=row["trip_name"],
        hotel_id=row["hotel_id"],
        hotel_name=row["hotel_name"],
        city=row["city"],
        state=row["state"],
        check_in=row["check_in"],
        check_out=row["check_out"],
        nightly_rate_usd=row["nightly_rate_usd"],
    )
    return {
        "booking_id": row["booking_id"],
        "user_id": row["user_id"],
        "display_name": row["display_name"],
        "booked_on": row["booked_on"],
        "status": row["status"],
        "stay": stay,
    }


def list_users(connection: sqlite3.Connection) -> list[dict[str, str]]:
    rows = connection.execute(
        "SELECT user_id, display_name FROM users ORDER BY user_id"
    ).fetchall()
    return [
        {"user_id": row["user_id"], "display_name": row["display_name"]}
        for row in rows
    ]


def get_booking(
    connection: sqlite3.Connection,
    booking_id: str,
) -> dict[str, object]:
    normalized_booking_id = booking_id.strip()
    if not normalized_booking_id:
        raise InvalidBookingRequestError("booking_id is required.")

    row = connection.execute(
        f"{BOOKING_SELECT} WHERE bookings.booking_id = ?",
        (normalized_booking_id,),
    ).fetchone()
    if row is None:
        raise BookingNotFoundError(
            f"Booking {normalized_booking_id} was not found."
        )
    return _booking_record(row)


def list_traveler_bookings(
    connection: sqlite3.Connection,
    user_id: str,
) -> dict[str, object]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise InvalidBookingRequestError("user_id is required.")

    user = connection.execute(
        "SELECT user_id, display_name FROM users WHERE user_id = ?",
        (normalized_user_id,),
    ).fetchone()
    if user is None:
        raise UserNotFoundError(f"Traveler {normalized_user_id} was not found.")

    rows = connection.execute(
        f"""
        {BOOKING_SELECT}
        WHERE bookings.user_id = ?
        ORDER BY bookings.booked_on DESC, bookings.booking_id DESC
        """,
        (normalized_user_id,),
    ).fetchall()
    return {
        "user_id": user["user_id"],
        "display_name": user["display_name"],
        "bookings": [_booking_record(row) for row in rows],
    }


def create_booking(
    connection: sqlite3.Connection,
    user_id: str,
    trip_id: str,
    booked_on: str | None = None,
) -> dict[str, object]:
    normalized_user_id = user_id.strip()
    normalized_trip_id = trip_id.strip()
    if not normalized_user_id or not normalized_trip_id:
        raise InvalidBookingRequestError("user_id and trip_id are required.")

    booking_date = booked_on or date.today().isoformat()
    try:
        date.fromisoformat(booking_date)
    except ValueError as error:
        raise InvalidBookingRequestError(
            "booked_on must use YYYY-MM-DD format."
        ) from error

    try:
        connection.execute("BEGIN IMMEDIATE")
        user_exists = connection.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (normalized_user_id,)
        ).fetchone()
        if user_exists is None:
            raise UserNotFoundError(f"Traveler {normalized_user_id} was not found.")

        trip_exists = connection.execute(
            "SELECT 1 FROM trips WHERE trip_id = ?", (normalized_trip_id,)
        ).fetchone()
        if trip_exists is None:
            raise TripNotFoundError(f"Trip {normalized_trip_id} was not found.")

        sequence = connection.execute(
            "SELECT next_number FROM booking_id_sequence WHERE singleton = 1"
        ).fetchone()
        if sequence is None:
            raise RuntimeError("Booking ID sequence is not initialized.")

        next_number = sequence["next_number"]
        booking_id = format_booking_id(next_number)
        while connection.execute(
            "SELECT 1 FROM bookings WHERE booking_id = ?", (booking_id,)
        ).fetchone() is not None:
            next_number += 1
            booking_id = format_booking_id(next_number)

        connection.execute(
            "UPDATE booking_id_sequence SET next_number = ? WHERE singleton = 1",
            (next_number + 1,),
        )
        connection.execute(
            """
            INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status)
            VALUES (?, ?, ?, ?, 'confirmed')
            """,
            (booking_id, normalized_user_id, normalized_trip_id, booking_date),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    return get_booking(connection, booking_id)


def cancel_booking(
    connection: sqlite3.Connection,
    booking_id: str,
) -> dict[str, object]:
    normalized_booking_id = booking_id.strip()
    if not normalized_booking_id:
        raise InvalidBookingRequestError("booking_id is required.")

    try:
        connection.execute("BEGIN IMMEDIATE")
        result = connection.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?",
            (normalized_booking_id,),
        )
        if result.rowcount == 0:
            raise BookingNotFoundError(
                f"Booking {normalized_booking_id} was not found."
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    return get_booking(connection, normalized_booking_id)


def delete_booking(connection: sqlite3.Connection, booking_id: str) -> str:
    normalized_booking_id = booking_id.strip()
    if not normalized_booking_id:
        raise InvalidBookingRequestError("booking_id is required.")

    try:
        connection.execute("BEGIN IMMEDIATE")
        result = connection.execute(
            "DELETE FROM bookings WHERE booking_id = ?", (normalized_booking_id,)
        )
        if result.rowcount == 0:
            raise BookingNotFoundError(
                f"Booking {normalized_booking_id} was not found."
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    return normalized_booking_id
