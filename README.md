# Expedia Lite

Expedia Lite is a local Vue and FastAPI travel application. Its ZIP workflow reads saved hotels first and falls back to Geoapify for hotels within 5 km only when local storage has no matches. Either result source appears in the same synchronized list and Leaflet map. A retrieval-augmented insights panel answers questions from saved provider locations and clearly labeled simulated nightly data through two backend-only requests to one configured OpenRouter model, with validated SQL execution between them. The existing classroom-data workflow also searches supplied stays and lets a selected demo traveler create, review, cancel, and permanently delete bookings stored in SQLite.

## Application flow

1. A visitor enters exactly five U.S. ZIP digits. Vue first requests saved hotels for that ZIP from FastAPI; the browser never receives the Geoapify credential.
2. When saved hotels exist, Vue renders their current committed nightly values and stored coordinates without making the Part 1 hotel-search request. When the saved lookup succeeds with zero matches, Vue requests the Part 1 search instead.
3. For a Part 1 search, FastAPI confirms an exact U.S. postcode match, then uses that returned coordinate as the center of a Geoapify Places query for `accommodation.hotel` within a 5,000-metre circle.
4. Vue renders either result source in one synchronized list and Leaflet map. Selecting either a row or marker selects the same `place_id` in both views. API hotels can be added locally, while saved hotels can be removed.
5. A saved-hotel question goes to FastAPI. The configured model first proposes one SQL `SELECT`; FastAPI validates it with a deny-by-default SQLite authorizer, executes it under work/result limits, then sends the exact retrieved rows to the same model for the grounded answer.
6. Separately, FastAPI initializes the SQLite schema on startup. A dedicated marker imports the four supplied CSV files only once for the life of that database file.
7. A traveler can search the supplied stays, book a result, review history, cancel while retaining the row, or permanently delete through an in-page confirmation.

After the initial seed completes, SQLite is the source of truth. Request paths do not read the CSV files, so refreshes and process restarts preserve new, cancelled, and deleted state.

## Project structure

```text
backend/app/              FastAPI boundary, provider services, SQLite data access, and rules
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

Set `GEOAPIFY_API_KEY` only in `backend/.env`. Revised Part 2 also needs:

```dotenv
OPENROUTER_API_KEY=<your local OpenRouter key>
OPENROUTER_MODEL=<the exact free Nemotron model slug demonstrated in class>
```

The exact class model slug is not present in the available repository or course attachment and is intentionally not guessed. Confirm the exact class-provided entry is still free in the live OpenRouter catalog before entering it. Expedia Lite accepts only an explicit NVIDIA Nemotron `:free` model setting and has no automatic or paid fallback. Do not put either provider key in `frontend/.env`, Vue source, or a `VITE_` variable; `VITE_` values are bundled for the browser.

`backend/app/geocoding.py` owns exact U.S. postcode confirmation, while `backend/app/places.py` owns the 5 km hotel query and provider normalization. `GET /api/hotels?zip=02108` runs the complete workflow. A successful response includes the confirmed search center, radius, count, and only real available Geoapify hotel fields. Invalid, unresolved, zero-result, configuration, timeout, and upstream-failure outcomes remain distinguishable. The earlier ZIP-only demonstration endpoints remain available for compatibility.

### Local hotel storage backend

The additive local-storage API keeps provider hotels separate from the supplied
Assignment 1 `hotels` table:

- `GET /api/saved-hotels?zip=02108` reads saved hotels associated with the
  searched ZIP and their current nightly records. A successful lookup with no
  matches returns `count: 0` and an empty `hotels` list.
- `POST /api/saved-hotels` accepts `searched_zip` and one existing provider
  `hotel` object. It saves one stable `place_id`, preserves every searched-ZIP
  association, and creates nights for October 10–14, 2026 only when those
  hotel/date rows do not already exist.
- `DELETE /api/saved-hotels/{place_id}` removes only that saved provider hotel;
  its ZIP associations and demo nights are deleted through enforced foreign
  keys.

`demo_hotel_nights` supplies database defaults of 10,000 cents and 20 rooms.
Repeated saves never replace a hotel or overwrite an existing nightly rate or
room count. Each request opens a fresh SQLite connection, so a committed edit
made in DB Browser is visible on the next lookup without restarting FastAPI.

### Saved hotel business intelligence

`POST /api/hotel-insights` accepts one question of at most 500 characters. The first backend-only OpenRouter request may return either an insufficient-data outcome or one proposed SQLite `SELECT`. FastAPI rejects semicolons, comments, non-`SELECT` statements, unauthorized tables/functions, writes, administrative/extension operations, excess query work, and oversized results. SQLite's authorizer permits reads only from `saved_hotels`, `saved_hotel_zips`, and `demo_hotel_nights`, so Assignment 1 travelers, bookings, trips, and supplied hotel rows cannot enter the model context.

After successful validation, FastAPI executes the bounded query. Even an empty result proceeds to request two so the model can return a grounded `no_matches` outcome. Nonempty results, the exact validated SQL, and the original question go to request two; the response includes an auditable trace containing the proposed SQL and the exact retrieved records. Out-of-coverage questions can return `insufficient_data` before SQL, while unsafe proposals return `rejected_query` without execution or request two. Provider location data is not proof of real hotel inventory, and every nightly rate, room count, and total remains labeled as simulated course data.

The current [research](docs/revised-part2-rag-research.md), [pre-implementation chatbot mockup](docs/revised-part2-chatbot-early-mockup.html), [dated evidence log](docs/revised-part2-evidence-log-2026-10-07.md), and [demo script](docs/revised-part2-demo-script.md) document the revised assignment.

### Frontend

In a second terminal, from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://127.0.0.1:5173`.

The frontend uses `http://127.0.0.1:8000` by default. To use another backend URL, create `frontend/.env` containing `VITE_API_URL=https://example.test`. Every explicit ZIP search sends `GET /api/saved-hotels?zip=<ZIP>` with browser caching disabled. A valid nonempty response is labeled **Saved locally** and prevents any Part 1 hotel search; only a valid empty response falls back to `GET /api/hotels?zip=<ZIP>` and is labeled **API results**. Local lookup failures remain errors and never trigger fallback.

Unsaved API records offer **Add to Local**. Persisted records offer **Remove from Local** and display the five simulated classroom nights with their actual stored rates and room counts. Repeating a search rereads committed SQLite values, including zero rates or room counts. Hotel names, addresses, distances, and coordinates are rendered only when supplied by the relevant backend response; the shared list and map remain synchronized for both result sources.

## Checks

With dependencies installed:

```bash
backend/.venv/bin/python -m pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run build
```

The deterministic revised-Part-2 sample is labeled fixture-only at
`backend/tests/fixtures/revised_part2_fixed_sample.json`. Run its complete RAG
and SQL-safety checks with:

```bash
cd backend
.venv/bin/python -m pytest -q tests/test_hotel_insights.py
.venv/bin/python scripts/revised_part2_fixture_demo.py
```

The second command prints the rejected-query fixture, proves no generated
write ran, reports zero second-model calls, compares protected data before and
after, and removes its temporary database automatically.

For the live-search checks and the complete browser CRUD, refresh, full-restart, database-count, screenshot, and console procedures, see [docs/verification.md](docs/verification.md).

Part 1 submission artifacts include the
[focused research](docs/part1-location-research.md),
[pre-implementation mockup](docs/part1-live-hotel-search-mockup.html),
[dated verification evidence](docs/part1-verification-2026-09-29.md),
[demo script](docs/part1-demo-script.md), and
[final rubric audit](docs/part1-final-audit.md).

The database baseline, pre-migration backup, schema choices, and isolated
verification for the local-hotel activity are recorded in
[local-hotel-storage-verification-2026-10-06.md](docs/local-hotel-storage-verification-2026-10-06.md).
The required DB Browser/browser evidence sequence is in the
[manual demonstration guide](docs/local-hotel-storage-manual-demo.md), with a
[submission draft](docs/local-hotel-storage-submission-draft.md) that keeps
unfinished observations as explicit placeholders.

## Current limitations

The project is intended for local classroom use. Geoapify results and counts can change as its place data changes. The exact class OpenRouter model slug and a local OpenRouter API key are still required for a genuine live-model demo; the implementation does not guess or fall back to a paid model. The application does not include authentication, authorization, production deployment controls, vector retrieval, embeddings, agent behavior, actual inventory, or an automated Vue component/end-to-end suite.
