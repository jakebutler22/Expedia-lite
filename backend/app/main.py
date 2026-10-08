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
from .config import geoapify_api_key_status, openrouter_configuration_status
from .database import (
    DATA_DIRECTORY,
    DEFAULT_DATABASE_PATH,
    connect_database,
    initialize_database,
)
from .domain import normalize_search_term
from .geocoding import (
    GeoapifyHTTPError,
    GeoapifyNetworkError,
    GeoapifyNotConfiguredError,
    GeoapifyResponseError,
    GeoapifyTimeoutError,
    InvalidPostcodeError,
    lookup_us_postcode,
)
from .hotel_search import search_hotels_by_postcode
from .hotel_insights import (
    InvalidInsightQuestionError,
    answer_saved_hotel_question,
)
from .models import (
    Booking,
    BookingCreate,
    BookingDeleteResponse,
    BookingHistoryResponse,
    Hotel,
    HotelInsightQuestion,
    HotelInsightResponse,
    HotelSearchResponse,
    SavedHotel,
    SavedHotelCreate,
    SavedHotelDeleteResponse,
    SavedHotelLookupResponse,
    SearchResponse,
    User,
    ZipLocationResponse,
)
from .openrouter import (
    OpenRouterHTTPError,
    OpenRouterNetworkError,
    OpenRouterNotConfiguredError,
    OpenRouterRateLimitError,
    OpenRouterResponseError,
    OpenRouterTimeoutError,
)
from .saved_hotels import (
    InvalidSavedHotelRequestError,
    SavedHotelNotFoundError,
    list_saved_hotels_by_zip,
    remove_saved_hotel,
    save_provider_hotel,
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


def _raise_saved_hotel_http_error(
    error: Exception,
    operation: str,
) -> NoReturn:
    if isinstance(error, InvalidSavedHotelRequestError):
        raise HTTPException(status_code=400, detail=str(error)) from error
    if isinstance(error, SavedHotelNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, sqlite3.Error):
        raise HTTPException(
            status_code=500,
            detail=f"Saved hotel {operation} failed.",
        ) from None
    raise error


def _lookup_zip_location(postcode: str) -> ZipLocationResponse:
    try:
        result = lookup_us_postcode(postcode)
    except InvalidPostcodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a five-digit U.S. ZIP code.",
        ) from None
    except GeoapifyNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Geoapify service is not configured.",
        ) from None
    except GeoapifyTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Geoapify ZIP lookup timed out.",
        ) from None
    except (
        GeoapifyNetworkError,
        GeoapifyHTTPError,
        GeoapifyResponseError,
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Geoapify ZIP lookup failed.",
        ) from None

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ZIP code {postcode.strip()} could not be resolved.",
        )

    return ZipLocationResponse(**result)


def _search_live_hotels(postcode: str) -> HotelSearchResponse:
    try:
        result = search_hotels_by_postcode(postcode)
    except InvalidPostcodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a five-digit U.S. ZIP code.",
        ) from None
    except GeoapifyNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Geoapify service is not configured.",
        ) from None
    except GeoapifyTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Geoapify hotel search timed out.",
        ) from None
    except (
        GeoapifyNetworkError,
        GeoapifyHTTPError,
        GeoapifyResponseError,
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Geoapify hotel search failed.",
        ) from None

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ZIP code {postcode.strip()} could not be resolved.",
        )

    hotels = [Hotel(**hotel) for hotel in result["hotels"]]
    return HotelSearchResponse(
        search_center=ZipLocationResponse(**result["search_center"]),
        radius_meters=result["radius_meters"],
        count=len(hotels),
        hotels=hotels,
    )


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
        description=(
            "Hotel search, saved-hotel business intelligence, and booking CRUD "
            "backed by SQLite."
        ),
        version="2.1.0",
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
        return {
            "status": "ok",
            "geoapify_api_key_status": geoapify_api_key_status(),
            **openrouter_configuration_status(),
        }

    @application.get(
        "/api/demo/zip-location",
        response_model=ZipLocationResponse,
        response_model_exclude_none=True,
    )
    def get_demo_zip_location() -> ZipLocationResponse:
        return _lookup_zip_location("16802")

    @application.get(
        "/api/zip-location",
        response_model=ZipLocationResponse,
        response_model_exclude_none=True,
    )
    def get_zip_location(
        zip: str = Query(
            ...,
            description="Five-digit U.S. ZIP code",
        ),
    ) -> ZipLocationResponse:
        return _lookup_zip_location(zip)

    @application.get(
        "/api/hotels",
        response_model=HotelSearchResponse,
        response_model_exclude_none=True,
    )
    def get_live_hotels(
        zip: str = Query(
            ...,
            description="Exact five-digit U.S. ZIP code used as the hotel search center",
        ),
    ) -> HotelSearchResponse:
        return _search_live_hotels(zip)

    @application.get(
        "/api/saved-hotels",
        response_model=SavedHotelLookupResponse,
    )
    def get_saved_hotels(
        connection: DatabaseConnection,
        zip: str = Query(
            ...,
            description="Searched five-digit U.S. ZIP association",
        ),
    ) -> SavedHotelLookupResponse:
        try:
            hotels = list_saved_hotels_by_zip(connection, zip)
        except (InvalidSavedHotelRequestError, sqlite3.Error) as error:
            _raise_saved_hotel_http_error(error, "lookup")

        normalized_zip = zip.strip()
        return SavedHotelLookupResponse(
            zip=normalized_zip,
            count=len(hotels),
            hotels=hotels,
        )

    @application.post(
        "/api/saved-hotels",
        response_model=SavedHotel,
        status_code=status.HTTP_201_CREATED,
    )
    def post_saved_hotel(
        saved_hotel: SavedHotelCreate,
        connection: DatabaseConnection,
    ) -> dict[str, object]:
        try:
            return save_provider_hotel(
                connection,
                saved_hotel.searched_zip,
                saved_hotel.hotel.model_dump(exclude_none=True),
            )
        except (InvalidSavedHotelRequestError, sqlite3.Error) as error:
            _raise_saved_hotel_http_error(error, "save")

    @application.delete(
        "/api/saved-hotels/{place_id}",
        response_model=SavedHotelDeleteResponse,
    )
    def delete_saved_hotel(
        place_id: str,
        connection: DatabaseConnection,
    ) -> SavedHotelDeleteResponse:
        try:
            deleted_place_id = remove_saved_hotel(connection, place_id)
        except (
            InvalidSavedHotelRequestError,
            SavedHotelNotFoundError,
            sqlite3.Error,
        ) as error:
            _raise_saved_hotel_http_error(error, "removal")
        return SavedHotelDeleteResponse(
            place_id=deleted_place_id,
            deleted=True,
        )

    @application.post(
        "/api/hotel-insights",
        response_model=HotelInsightResponse,
        response_model_exclude_none=True,
    )
    def post_hotel_insight(
        insight: HotelInsightQuestion,
        connection: DatabaseConnection,
    ) -> dict[str, object]:
        try:
            return answer_saved_hotel_question(connection, insight.question)
        except InvalidInsightQuestionError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except OpenRouterNotConfiguredError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter insights service is not configured.",
            ) from None
        except OpenRouterTimeoutError as error:
            stage = (
                "SQL generation"
                if error.stage == "sql_generation"
                else "answer generation"
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"OpenRouter {stage} timed out.",
            ) from None
        except OpenRouterRateLimitError as error:
            stage = (
                "SQL generation"
                if error.stage == "sql_generation"
                else "answer generation"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"OpenRouter {stage} is temporarily rate limited.",
            ) from None
        except (
            OpenRouterNetworkError,
            OpenRouterHTTPError,
            OpenRouterResponseError,
        ) as error:
            stage = (
                "SQL generation"
                if error.stage == "sql_generation"
                else "answer generation"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenRouter {stage} failed.",
            ) from None
        except sqlite3.Error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Saved hotel insights lookup failed.",
            ) from None

    @application.get("/api/stays", response_model=SearchResponse)
    def get_stays(
        connection: DatabaseConnection,
        query: str | None = Query(
            None,
            description="Hotel name or city, matched case-insensitively",
        ),
        city: str | None = Query(
            None,
            deprecated=True,
            description="Deprecated alias for query; matches a hotel name or city",
        ),
    ) -> SearchResponse:
        search_query = query if query is not None else city
        if search_query is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Provide query with a hotel name or city.",
            )

        try:
            stays = search_stays(connection, search_query)
        except InvalidSearchQueryError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        normalized_query = normalize_search_term(search_query)
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
