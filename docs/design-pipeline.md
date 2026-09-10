# Expedia Lite design pipeline

## Responsibilities

- **Vue frontend (`frontend/`)** owns the city input, Search button, loading/error/empty states, and accessible results table. It does not read CSV files directly.
- **FastAPI boundary (`backend/app/main.py`)** validates the request, enables local frontend access with CORS, and returns a documented JSON response.
- **Python search service (`backend/app/search.py`)** reads both CSV files with BOM-safe UTF-8 handling, joins hotels to trips by `hotel_id`, performs a trimmed case-insensitive city match, and calculates nights and estimated stay price.
- **CSV data (`backend/data/`)** is read-only source data for Part 1. There is no persistence layer until Part 2.

## Request pipeline

```text
City input + Search
        |
        v
GET /api/stays?city=Boston
        |
        v
FastAPI validates the city
        |
        v
Python reads hotels.csv + trips.csv
        |
        v
hotel_id join -> city filter -> derived price
        |
        v
JSON response -> Vue table or no-results state
```

## Response shape

The endpoint returns the normalized display query, result count, and a list of enriched stays. Each stay contains trip and hotel IDs/names, location, dates, night count, nightly rate, and estimated stay price.

## Part 2 boundary

Part 2 will introduce SQLite, seed all four supplied CSVs once, and add booking CRUD endpoints and frontend workflows. Those responsibilities are intentionally absent from Part 1.
