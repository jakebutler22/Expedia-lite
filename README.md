# Expedia Lite

Expedia Lite is a local Vue and FastAPI travel application. It searches supplied hotel stays by hotel name or city and lets a selected demo traveler create, review, cancel, and permanently delete bookings stored in SQLite.

## Application flow

1. FastAPI initializes the SQLite schema on startup. A dedicated marker causes the four supplied CSV files to be imported only once for the life of that database file.
2. A traveler selects a demo user and searches by a full or partial hotel name, or by city, in the Vue frontend.
3. Vue calls FastAPI; FastAPI delegates search and booking operations to framework-free Python modules that read and write SQLite.
4. A stay can be booked directly from the results table. Booking history shows joined hotel and trip details, dates, and status.
5. Cancelling retains the booking with status `cancelled`. Deleting requires an in-page confirmation and permanently removes the row.

After the initial seed completes, SQLite is the source of truth. Request paths do not read the CSV files, so refreshes and process restarts preserve new, cancelled, and deleted state.

## Project structure

```text
backend/app/              FastAPI boundary, SQLite initialization, data access, and rules
backend/data/             Four immutable seed CSVs and the ignored runtime database
backend/tests/            Fresh-database persistence, search, API, and lifecycle tests
frontend/                 Vue search and booking CRUD interface
docs/                     Design and verification records
prompts/                  Selected numbered development prompts
handoffs/current.md       Current project state and next task
report.md                 Part 2 submission report
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

### Frontend

In a second terminal, from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://127.0.0.1:5173`.

The frontend uses `http://127.0.0.1:8000` by default. To use another backend URL, create `frontend/.env` containing `VITE_API_URL=https://example.test`.

## Checks

With dependencies installed:

```bash
backend/.venv/bin/python -m pytest backend/tests
npm --prefix frontend run build
```

For the complete browser CRUD, refresh, full-restart, database-count, screenshot, and console procedure, see [docs/verification.md](docs/verification.md).

## Current limitations

Part 2 is intended for local classroom use with six demo travelers and one SQLite database file. It does not include authentication, authorization, production deployment controls, or automated Vue component/end-to-end tests.
