from typing import Literal

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
