from datetime import date


def normalize_search_term(value: str) -> str:
    return value.strip()


def escape_like_pattern(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def calculate_stay(
    check_in_value: str,
    check_out_value: str,
    nightly_rate_value: float,
) -> tuple[int, float]:
    check_in = date.fromisoformat(check_in_value)
    check_out = date.fromisoformat(check_out_value)
    nights = (check_out - check_in).days
    nightly_rate = float(nightly_rate_value)
    return nights, nightly_rate * nights


def build_stay_record(
    *,
    trip_id: str,
    trip_name: str,
    hotel_id: str,
    hotel_name: str,
    city: str,
    state: str,
    check_in: str,
    check_out: str,
    nightly_rate_usd: float,
) -> dict[str, str | int | float]:
    nights, stay_price = calculate_stay(check_in, check_out, nightly_rate_usd)
    return {
        "trip_id": trip_id,
        "trip_name": trip_name,
        "hotel_id": hotel_id,
        "hotel_name": hotel_name,
        "city": city,
        "state": state,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "nightly_rate_usd": float(nightly_rate_usd),
        "stay_price_usd": stay_price,
    }


def format_booking_id(number: int) -> str:
    if number < 1:
        raise ValueError("Booking numbers must be positive.")
    return f"B{number:03d}"
