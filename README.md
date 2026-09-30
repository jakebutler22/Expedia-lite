# Expedia Lite

Expedia Lite is a local Vue and FastAPI travel application. Its live search confirms a five-digit U.S. ZIP through Geoapify, finds hotels within 5 km, and presents the same provider results in a synchronized list and Leaflet map. The existing classroom-data workflow also searches supplied stays and lets a selected demo traveler create, review, cancel, and permanently delete bookings stored in SQLite.

## Application flow

1. A visitor enters exactly five U.S. ZIP digits. Vue calls only FastAPI; the browser never receives the Geoapify credential.
2. FastAPI confirms an exact U.S. postcode match, then uses that returned coordinate as the center of a Geoapify Places query for `accommodation.hotel` within a 5,000-metre circle.
3. Vue renders the normalized provider results in one list and one Leaflet map. Selecting either a row or marker selects the same `place_id` in both views.
4. Separately, FastAPI initializes the SQLite schema on startup. A dedicated marker imports the four supplied CSV files only once for the life of that database file.
5. A traveler can search the supplied stays, book a result, review history, cancel while retaining the row, or permanently delete through an in-page confirmation.

After the initial seed completes, SQLite is the source of truth. Request paths do not read the CSV files, so refreshes and process restarts preserve new, cancelled, and deleted state.

## Project structure

```text
backend/app/              FastAPI boundary, Geoapify services, SQLite data access, and rules
backend/data/             Four immutable seed CSVs and the ignored runtime database
backend/tests/            Fresh-database persistence, search, API, and lifecycle tests
frontend/                 Vue search and booking CRUD interface
docs/                     Design and verification records
prompts/                  Selected numbered development prompts
handoffs/current.md       Current project state and next task
report.md                 Part 1 implementation report and preserved Part 2 report
```

## Setup

Prerequisites: Python 3.11 or newer and Node.js 20.19 or newer.

### Backend

From the project root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is at `http://127.0.0.1:8000/docs`. The first startup creates the ignored `backend/data/expedia-lite.db` file and seeds it from all four CSV files. Later startups use the existing database without re-importing the CSVs.

### Backend configuration

Backend configuration is loaded from ignored `backend/.env`. Copy the safe template, add your real key locally, and restart the backend after changing it:

```bash
cp backend/.env.example backend/.env
```

Set `GEOAPIFY_API_KEY` only in `backend/.env`. Do not put it in `frontend/.env`, Vue source, or a `VITE_` variable; `VITE_` values are bundled for the browser.

`backend/app/geocoding.py` owns exact U.S. postcode confirmation, while `backend/app/places.py` owns the 5 km hotel query and provider normalization. `GET /api/hotels?zip=02108` runs the complete workflow. A successful response includes the confirmed search center, radius, count, and only real available Geoapify hotel fields. Invalid, unresolved, zero-result, configuration, timeout, and upstream-failure outcomes remain distinguishable. The earlier ZIP-only demonstration endpoints remain available for compatibility.

### Frontend

In a second terminal, from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://127.0.0.1:5173`.

The frontend uses `http://127.0.0.1:8000` by default. To use another backend URL, create `frontend/.env` containing `VITE_API_URL=https://example.test`. The live search shows loading, results, invalid, unresolved, zero-result, and failed-request states. Hotel names, addresses, distances, and coordinates are rendered only when supplied by the backend response; no price, rating, availability, or booking claim is added to live results.

## Checks

With dependencies installed:

```bash
backend/.venv/bin/python -m pytest backend/tests
npm --prefix frontend run build
```

For the live-search checks and the complete browser CRUD, refresh, full-restart, database-count, screenshot, and console procedures, see [docs/verification.md](docs/verification.md).

Part 1 submission artifacts include the
[focused research](docs/part1-location-research.md),
[pre-implementation mockup](docs/part1-live-hotel-search-mockup.html),
[dated verification evidence](docs/part1-verification-2026-09-29.md),
[demo script](docs/part1-demo-script.md), and
[final rubric audit](docs/part1-final-audit.md).

## Current limitations

The project is intended for local classroom use. Geoapify results and counts can change as its place data changes. The application does not include authentication, authorization, production deployment controls, or an automated Vue component/end-to-end suite.
