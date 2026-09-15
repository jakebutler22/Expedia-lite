import sqlite3
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, NoReturn

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

from .bookings import (
    BookingNotFoundError,
    InvalidBookingRequestError,
    TripNotFoundError,
    UserNotFoundError,
    cancel_booking,
    create_booking,
    delete_booking,
    get_booking,
    list_traveler_bookings,
    list_users,
)
from .database import (
    DATA_DIRECTORY,
    DEFAULT_DATABASE_PATH,
    connect_database,
    initialize_database,
)
from .domain import normalize_search_term
from .models import (
    Booking,
    BookingCreate,
    BookingDeleteResponse,
    BookingHistoryResponse,
    SearchResponse,
    User,
)
from .search import InvalidSearchQueryError, search_stays


def database_connection(request: Request) -> Iterator[sqlite3.Connection]:
    connection = connect_database(request.app.state.database_path)
    try:
        yield connection
    finally:
        connection.close()


DatabaseConnection = Annotated[sqlite3.Connection, Depends(database_connection)]


def _raise_booking_http_error(error: Exception) -> NoReturn:
    if isinstance(error, InvalidBookingRequestError):
        raise HTTPException(status_code=400, detail=str(error)) from error
    if isinstance(
        error, (BookingNotFoundError, TripNotFoundError, UserNotFoundError)
    ):
        raise HTTPException(status_code=404, detail=str(error)) from error
    raise error


def create_app(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    data_directory: str | Path = DATA_DIRECTORY,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        initialize_database(database_path, data_directory)
        yield

    application = FastAPI(
        title="Expedia Lite API",
        description="Hotel search and booking CRUD backed by SQLite.",
        version="2.0.0",
        lifespan=lifespan,
    )
    application.state.database_path = Path(database_path)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    @application.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/api/stays", response_model=SearchResponse)
    def get_stays(
        connection: DatabaseConnection,
        city: str = Query(
            ...,
            description="Hotel name or full city name, matched case-insensitively",
        ),
    ) -> SearchResponse:
        try:
            stays = search_stays(connection, city)
        except InvalidSearchQueryError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        normalized_query = normalize_search_term(city)
        return SearchResponse(
            query=normalized_query,
            count=len(stays),
            stays=stays,
        )

    @application.get("/api/users", response_model=list[User])
    def get_users(connection: DatabaseConnection) -> list[dict[str, str]]:
        return list_users(connection)

    @application.get(
        "/api/users/{user_id}/bookings",
        response_model=BookingHistoryResponse,
    )
    def get_traveler_bookings(
        user_id: str,
        connection: DatabaseConnection,
    ) -> BookingHistoryResponse:
        try:
            history = list_traveler_bookings(connection, user_id)
        except (InvalidBookingRequestError, UserNotFoundError) as error:
            _raise_booking_http_error(error)

        bookings = history["bookings"]
        return BookingHistoryResponse(
            user_id=history["user_id"],
            display_name=history["display_name"],
            count=len(bookings),
            bookings=bookings,
        )

    @application.get("/api/bookings/{booking_id}", response_model=Booking)
    def get_booking_by_id(
        booking_id: str,
        connection: DatabaseConnection,
    ) -> dict[str, object]:
        try:
            return get_booking(connection, booking_id)
        except (InvalidBookingRequestError, BookingNotFoundError) as error:
            _raise_booking_http_error(error)

    @application.post(
        "/api/bookings",
        response_model=Booking,
        status_code=status.HTTP_201_CREATED,
    )
    def post_booking(
        booking: BookingCreate,
        connection: DatabaseConnection,
    ) -> dict[str, object]:
        try:
            return create_booking(connection, booking.user_id, booking.trip_id)
        except (
            InvalidBookingRequestError,
            TripNotFoundError,
            UserNotFoundError,
        ) as error:
            _raise_booking_http_error(error)

    @application.patch(
        "/api/bookings/{booking_id}/cancel",
        response_model=Booking,
    )
    def patch_booking_cancel(
        booking_id: str,
        connection: DatabaseConnection,
    ) -> dict[str, object]:
        try:
            return cancel_booking(connection, booking_id)
        except (InvalidBookingRequestError, BookingNotFoundError) as error:
            _raise_booking_http_error(error)

    @application.delete(
        "/api/bookings/{booking_id}",
        response_model=BookingDeleteResponse,
    )
    def remove_booking(
        booking_id: str,
        connection: DatabaseConnection,
    ) -> BookingDeleteResponse:
        try:
            deleted_booking_id = delete_booking(connection, booking_id)
        except (InvalidBookingRequestError, BookingNotFoundError) as error:
            _raise_booking_http_error(error)
        return BookingDeleteResponse(booking_id=deleted_booking_id, deleted=True)

    return application


app = create_app()
