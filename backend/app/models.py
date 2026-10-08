from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Stay(BaseModel):
    """A trip enriched with the hotel information shown by the frontend."""

    trip_id: str
    trip_name: str
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    check_in: str
    check_out: str
    nights: int
    nightly_rate_usd: float
    stay_price_usd: float


class SearchResponse(BaseModel):
    query: str
    count: int
    stays: list[Stay]


class ZipLocationResponse(BaseModel):
    postcode: str
    country_code: str
    latitude: float
    longitude: float
    locality: str | None = None


class Hotel(BaseModel):
    place_id: str
    name: str
    latitude: float
    longitude: float
    formatted_address: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postcode: str | None = None
    country: str | None = None
    distance_meters: float | None = None
    categories: list[str] | None = None


class SavedProviderHotel(Hotel):
    address: str | None = None


class HotelSearchResponse(BaseModel):
    search_center: ZipLocationResponse
    radius_meters: int
    count: int
    hotels: list[Hotel]


class SavedHotelCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    searched_zip: str = Field(min_length=1)
    hotel: SavedProviderHotel


class DemoHotelNight(BaseModel):
    date: str
    nightly_rate_cents: int
    rooms_available: int


class SavedHotel(BaseModel):
    place_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    searched_zips: list[str]
    nights: list[DemoHotelNight]


class SavedHotelLookupResponse(BaseModel):
    zip: str
    count: int
    hotels: list[SavedHotel]


class SavedHotelDeleteResponse(BaseModel):
    place_id: str
    deleted: bool


class HotelInsightQuestion(BaseModel):
    question: str


class HotelInsightTrace(BaseModel):
    model: str
    proposed_sql: str | None
    validation_status: Literal["not_run", "passed", "rejected"]
    query_executed: bool
    retrieved_records: list[dict[str, Any]]
    second_request_sent: bool


class HotelInsightResponse(BaseModel):
    status: Literal[
        "answer",
        "no_matches",
        "insufficient_data",
        "rejected_query",
    ]
    question: str
    count: int
    records: list[dict[str, Any]]
    answer: str | None = None
    message: str | None = None
    model: str | None = None
    trace: HotelInsightTrace


class User(BaseModel):
    user_id: str
    display_name: str


class BookingCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str = Field(min_length=1)
    trip_id: str = Field(min_length=1)


class Booking(BaseModel):
    booking_id: str
    user_id: str
    display_name: str
    booked_on: str
    status: Literal["confirmed", "cancelled"]
    stay: Stay


class BookingHistoryResponse(BaseModel):
    user_id: str
    display_name: str
    count: int
    bookings: list[Booking]


class BookingDeleteResponse(BaseModel):
    booking_id: str
    deleted: bool
