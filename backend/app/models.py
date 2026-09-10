from pydantic import BaseModel


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
