# Expedia Lite design pipeline

## Responsibilities

- **Vue frontend (`frontend/`)** owns the hotel-or-city input, selected demo traveler, stay results, booking history, loading/error/empty states, and the visibly distinct booking, cancellation, and in-page deletion controls. It communicates only with FastAPI and never opens CSV or SQLite files.
- **FastAPI boundary (`backend/app/main.py`)** starts the database initializer, provides one SQLite connection per request, validates HTTP input and output, maps framework-free errors to useful status codes, and exposes search and booking CRUD endpoints.
- **Framework-free data access (`backend/app/search.py` and `backend/app/bookings.py`)** performs SQLite queries for stay search, traveler history, booking creation, cancellation, and deletion. It has no FastAPI dependency.
- **Framework-free rules (`backend/app/domain.py`)** normalize search text, escape SQL `LIKE` patterns, calculate nights and estimated prices, build enriched stay records, and format booking IDs.
- **SQLite initialization (`backend/app/database.py`)** creates the schema, enables foreign-key enforcement on every connection, imports all four CSV files only when the seed marker is absent, and initializes the persistent booking-ID sequence.
- **Supplied CSV data (`backend/data/*.csv`)** is immutable one-time seed input. After the first successful seed, SQLite is the sole source of truth.

## Startup and persistence pipeline

```text
FastAPI startup
      |
      v
Open SQLite connection + enable foreign keys
      |
      v
Create tables if needed
      |
      v
Is initial-csv-data marker present?
      | yes                         | no
      v                             v
Skip every CSV read        Read all four CSV files once
      |                    Insert starter rows + ID sequence
      |                    Record seed marker last
      +-----------------------------+
                    |
                    v
All request reads and writes use SQLite
```

The marker and starter inserts share one transaction. A failed import rolls back without recording completion; a completed import is never replayed. Consequently, restarting cannot duplicate starter rows, restore a deleted booking, or erase a booking created through the application.

## Search pipeline

```text
Hotel name or city + Search
            |
            v
GET /api/stays?city=<query>
            |
            v
FastAPI obtains a SQLite connection
            |
            v
One hotels/trips JOIN query
partial hotel-name match OR exact city match
            |
            v
Framework-free night and price calculation
            |
            v
JSON response -> Vue results table or no-results state
```

Hotel-name matching is trimmed, case-insensitive, and partial; city matching is trimmed, case-insensitive, and exact. The existing Part 1 table headings and calculated nights × nightly-rate price remain intact.

## Booking CRUD pipeline

| User action | HTTP boundary | Data operation | Visible result |
| --- | --- | --- | --- |
| Select a traveler | `GET /api/users` | Read users from SQLite. | The demo traveler selector is populated. |
| Open booking history | `GET /api/users/{user_id}/bookings` | Join bookings, trips, hotels, and users. | Full stay details, booked-on date, and status appear, or a clear empty state is shown. |
| Book a listed stay | `POST /api/bookings` | Validate the user and trip, reserve the next persistent ID, and insert a confirmed row atomically. | The assigned ID appears in the selected traveler's history. |
| Cancel a booking | `PATCH /api/bookings/{booking_id}/cancel` | Update status to `cancelled`. | The row remains visible with a cancelled badge. |
| Delete a booking | `DELETE /api/bookings/{booking_id}` | Permanently delete the row after in-page confirmation. | The row disappears from history. |

Booking IDs retain the supplied `B001` format. `booking_id_sequence` advances within the same write transaction as creation and never moves backward, so deleting a booking cannot cause its ID to be reused.

## Current boundaries

Part 2 fulfills local SQLite persistence and browser-accessible CRUD for supplied demo travelers. It does not provide authentication, authorization, multi-user deployment support, or automated Vue component/end-to-end tests. The current verification uses backend pytest coverage, the Vite production build, manual Source Control review, and the recorded browser SmokeTest.
