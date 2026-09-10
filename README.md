# Expedia Lite

Purpose: a local travel application with a Vue interface and Python backend. Part 1 searches the supplied hotel stays by city using CSV data.

## Application flow

1. A traveler enters a city in the Vue frontend and selects **Search**.
2. Vue sends `GET /api/stays?city=...` to FastAPI.
3. The Python search service reads `hotels.csv` and `trips.csv`, joins rows with the same `hotel_id`, and filters cities without regard to capitalization.
4. Vue presents the matching stays in a table or a clear no-results message.

## Project structure

```text
backend/                 FastAPI application, CSV data, and backend tests
frontend/                Vue application
docs/                    Design and verification notes
prompts/                 Selected development prompts
handoffs/current.md      Current project state and next task
report.md                Part 1 submission report
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

The API is available at `http://127.0.0.1:8000`. Its interactive documentation is at `http://127.0.0.1:8000/docs`.

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

For the browser procedure and expected data, see [docs/verification.md](docs/verification.md).

## Part 1 limitations

Part 1 reads CSV files on every search and does not create bookings or persist changes. SQLite booking CRUD is reserved for Part 2.
