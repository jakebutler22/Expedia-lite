from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import SearchResponse
from .search import search_stays


app = FastAPI(
    title="Expedia Lite API",
    description="Part 1 city search backed by the supplied CSV files.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/stays", response_model=SearchResponse)
def get_stays(
    city: str = Query(..., description="Full city name, matched case-insensitively"),
) -> SearchResponse:
    normalized_city = city.strip()
    if not normalized_city:
        raise HTTPException(status_code=400, detail="Enter a city to search.")

    stays = search_stays(normalized_city)
    return SearchResponse(query=normalized_city, count=len(stays), stays=stays)
