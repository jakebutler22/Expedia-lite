# Revised Assignment 2 Part 2 evidence log

This log began on October 7, 2026, before revised Part 2 chatbot implementation. Entries separate observed evidence from planned or pending work.

## E1 — Repository and protected-history baseline

- Branch: `main`, two commits ahead of `origin/main` at the start of the audit.
- HEAD: `3a08974502eaff083a5f81eb3c727d3508c8885c`.
- Protected checkpoints remained reachable: `part1-submission`, `part2-submission`, and `assignment-2.1-part1-assessed` (`de43dd9df5c7cc842e9693f29cd43cb85e43507a`).
- Material uncommitted local-storage work already existed in backend, frontend, tests, documentation, and handoff files. It was treated as user work and preserved.
- No backend or frontend listener occupied ports 8000 or 5173 during the initial audit.

## E2 — Read-only Assignment 1 data baseline

Canonical database: ignored `backend/data/expedia-lite.db`.

| Table | Observed state before revised Part 2 changes |
| --- | --- |
| `hotels` | 8 rows, H001–H008 |
| `trips` | 12 rows, T001–T012 |
| `users` | 6 rows, U001–U006 |
| `bookings` | 9 rows: B001, B002, B003, B004, B005, B007, B009, B011, B013 |
| `booking_id_sequence` | `next_number = 15` |
| `seed_metadata` | one `initial-csv-data` marker |
| `saved_hotels` | 0 rows |
| `saved_hotel_zips` | 0 rows |
| `demo_hotel_nights` | 0 rows |

The six original Assignment 1 tables matched the verified October 6 pre-local-storage backup in both directions. The CSV files were not used as the current-state authority; notably, the database correctly preserves a previously deleted booking and later classroom activity that differ from the original CSV fixture.

Initial active-database evidence:

- SHA-256: `c43f08bd015ddb73b498d0cff83b3e49ff251fbea4e485ceee0a7b38e5a75622`
- `PRAGMA integrity_check`: `ok`
- `PRAGMA foreign_key_check`: no rows

## E3 — Consistent pre-RAG backup

Before chatbot production changes, SQLite's backup API created the non-overwriting ignored file:

`backend/data/backups/expedia-lite-pre-rag-2026-10-07.db`

- SHA-256: `5fbc9303ad49f9b452aeecf20471de95db2d138645c73a21e115fd715b676166`
- Size: 77,824 bytes
- Backup integrity: `ok`
- Backup foreign-key check: no rows
- Counts matched all nine application tables.
- Bidirectional `EXCEPT` comparisons reported zero row differences for every application table.
- `sqlite_sequence` preserved `saved_hotels = 1`, evidence of a previously inserted and removed demonstration hotel without restoring it.
- The backup and directory remain excluded by `.gitignore`; no database file will be committed.

## E4 — Existing local-storage foundation

- `saved_hotels` preserves unique provider identity, name, address, latitude, and longitude.
- `saved_hotel_zips` preserves five-digit text ZIP associations, including leading zeroes, with hotel/ZIP uniqueness.
- `demo_hotel_nights` preserves hotel/date uniqueness and the hotel foreign-key relationship. Schema defaults are 10,000 cents and 20 rooms.
- Saving creates only October 10–14, 2026 rows with defaults; conflict handling does not overwrite later committed edits.
- Existing routes are `GET /api/saved-hotels`, `POST /api/saved-hotels`, and `DELETE /api/saved-hotels/{place_id}`.
- Existing frontend logic is local-first: nonempty local results skip Part 1 and display **Saved locally**; a valid empty local response falls back and displays **API results**; local failure stops without fallback.
- Existing UI labels nightly values as simulated classroom data.

## E5 — Environment and dependency check

- Backend already has Python 3.14.7, FastAPI 0.141.1, HTTPX 0.28.1, pytest 9.1.1, python-dotenv 1.2.3, and Uvicorn 0.52.4.
- Frontend already has Vue 3.5.42, Leaflet 1.9.4, Vite 8.2.2, and the Vue Vite plugin 6.0.8.
- Existing `httpx` can call OpenRouter's REST endpoint; built-in `sqlite3` provides retrieval and backup support. No dependency addition or upgrade is necessary.

## E6 — Provider and course-material audit

No OpenRouter key variable, model variable, Nemotron slug, chatbot implementation, RAG prompt, or chatbot mockup existed in the repository, its Git objects, or the neighboring readable course projects. The revised brief says only "the free Nemotron option through OpenRouter demonstrated in class."

The official live model catalog listed multiple free Nemotron choices on October 7, 2026. Therefore the exact class model cannot be inferred honestly. The implementation may accept an explicit backend setting, but live provider verification remains pending until the exact class slug and a local OpenRouter key are entered in ignored `backend/.env`.

## E7 — Pre-implementation artifacts

- Research: `docs/revised-part2-rag-research.md`
- Early chatbot mockup: `docs/revised-part2-chatbot-early-mockup.html`

Both were saved before production chatbot code was added. The earlier local-storage feature already existed in the dirty working tree; the chronology is not represented as if that foundation were created after this mockup.

## E8 — Superseded first implementation

This entry records the first implementation chronologically. It was later
superseded by the required two-request SQL pipeline in E12–E15; its one-request
architecture and the E9–E10 counts are not the final assessed implementation.

No schema migration was necessary after the verified backup. Revised Part 2 added:

- `backend/app/hotel_insights.py`: bounded, read-only retrieval with application-owned parameterized SQL and explicit `answer`, `no_matches`, and `insufficient_data` outcomes.
- `backend/app/openrouter.py`: one backend-only OpenRouter REST request, a free-Nemotron-only configuration guard, bounded input/output, sanitized timeout/network/HTTP/response errors, and a strict grounding prompt.
- `POST /api/hotel-insights`: the only new route. It never accepts SQL and never returns provider credentials or the full prompt.
- `frontend/src/hotelInsights.js`: the Vue request contract and response validation.
- A Vue **Saved hotel insights** panel with ready, loading, answer, invalid, no-match, insufficient-data, and failure states. Evidence records can select the same visible list item and map marker.
- Visible `Powered by Geoapify` attribution beside the map, in addition to the existing visible Leaflet/OpenStreetMap attribution inside it.

The retrieval query reads only `saved_hotels`, `saved_hotel_zips`, and `demo_hotel_nights`. It never reads Assignment 1 travelers, trips, bookings, or supplied-hotel rows into the LLM context. No vector database, embeddings, agent framework, new schema, paid fallback, actual booking capability, or new dependency was added.

## E9 — Superseded implementation checks

| Check | Expected | Observed | Result |
| --- | --- | --- | --- |
| Focused backend tests | Retrieval, leading-zero ZIP scope, grounding, no-match, insufficient-data, configuration, timeout/failure, malformed response, injection resistance, and credential isolation pass. | First run exposed a test-fixture mistake: temporary databases have six seed bookings while the canonical database has nine current bookings. Tests were revised to compare before/after values. Rerun: 23 focused saved-hotel/insights tests passed. | Pass after correction |
| Full backend suite | Existing and new backend behavior pass together. | 91 tests passed in 0.47 seconds; two existing dependency deprecation warnings were reported. | Pass |
| Frontend request tests | Local-first and insights request/state contracts pass without new packages. | 17 Node tests passed, including HTTP/network/malformed insight failures and distinct no-match/insufficient results. | Pass |
| Production frontend build | Vue compiles with no production error. | Vite 8.2.2 transformed 15 modules and built successfully in 122 ms. | Pass |
| Dependency loop | No install occurs unless necessary and approved. | Existing `httpx`, Vue, Leaflet, and built-in SQLite/Node testing were sufficient. No package was added, upgraded, or installed. | Pass |

The failed fixed-count test was a legitimate revised approach: the first assertion incorrectly applied the canonical nine-booking state to a fresh CSV-seeded test database. Replacing the fixed number with a captured before/after snapshot made the security test valid for both environments without changing application code or data.

## E10 — Superseded implementation smoke test

FastAPI and Vue were run on October 7, 2026. To protect the canonical database and avoid claiming unavailable live-provider evidence, the smoke run used:

- an isolated temporary SQLite database initialized by the real application;
- two clearly named temporary saved-hotel records created through the real API;
- the production Vue application and route contracts; and
- a process-local OpenRouter response stub with answer, insufficient-data, failure, and delayed-response behaviors.

The temporary database and both processes were removed/stopped after the run. The canonical ignored database was not opened by the smoke backend.

| Input/action | Expected | Observed | Result |
| --- | --- | --- | --- |
| Search `02108` | A local match is labeled **Saved locally** and no Part 1 fallback is needed. | Two current saved records loaded with leading-zero ZIP intact, five simulated nights each, and stored coordinates. | Pass |
| Inspect map attribution | Leaflet/data attribution remains visible. | `Leaflet | © OpenStreetMap contributors` remained in-map; `Powered by Geoapify` was visible below the map. | Pass |
| Ask a stored-rate question | Loading changes to a grounded answer with current evidence and honest simulated-data wording. | Delayed request visibly showed **Checking saved hotel facts…** and disabled/loading button text, then a one-model answer labeled the $100.00 value simulated and not live inventory. | Pass with stub; live provider pending |
| Ask about a rooftop pool | Missing property data becomes insufficient data, not a fabricated claim. | **Insufficient saved data** appeared and retained the retrieved evidence records. | Pass with stub |
| Ask about ZIP `16802` | No matching local facts avoid the provider and show no matches. | **No saved hotel matches** appeared with no evidence list. | Pass |
| Simulate provider HTTP failure | A clear failure state appears without breaking hotel search. | **Saved hotel insights unavailable** appeared with the sanitized error and the message that search/local storage remain available. | Pass with stub |
| Select the second evidence hotel | The same hotel becomes selected in the existing list and map. | Second Smoke Hotel's list control changed to `aria-pressed="true"`; exactly one marker had the selected class. | Pass |
| Keyboard-submit a question | Question form is usable without a pointer. | Tab from the question field followed by Enter submitted and reached the no-match result. | Pass |
| Inspect browser console | No application warnings or errors. | Zero warning/error entries. | Pass |

This smoke test is implementation evidence, not a live OpenRouter verification. A genuine live request remains blocked only by the missing exact class model slug and local OpenRouter API key.

## E11 — Security and preserved-state recheck

- Final canonical database SHA-256 remained `c43f08bd015ddb73b498d0cff83b3e49ff251fbea4e485ceee0a7b38e5a75622`, exactly the initial value. `integrity_check` remained `ok`, the foreign-key check remained empty, counts remained 8 hotels / 12 trips / 6 users / 9 bookings / sequence 15 / one seed marker / zero rows in each saved-hotel table, and bidirectional comparisons with the pre-RAG backup again found zero application-table differences.
- `backend/.env` remains ignored; `backend/.env.example` remains trackable and contains blank `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` placeholders.
- The frontend contains no provider key variable and makes no request to OpenRouter or Geoapify.
- The API health response contains configuration status phrases only, never values.
- The model setting must match an explicit NVIDIA Nemotron `:free` slug. Paid or non-Nemotron values fail as unconfigured; there is no silent model fallback.
- User question text and retrieved strings are serialized as data. Static SQL and bound parameters remain under application control. A test used SQL-looking text in both a question and saved hotel name; original tables and saved records remained intact.
- No database DDL was added for the chatbot. The pre-RAG backup remains the recovery point for the exact audited state.

## Genuinely missing live configuration

Enter the two local values in ignored `backend/.env`:

```dotenv
OPENROUTER_API_KEY=<your local OpenRouter key>
OPENROUTER_MODEL=<the exact free Nemotron slug demonstrated in class>
```

The model slug is not present in the available course/project materials and was not guessed. After it is supplied, verify that exact entry against the [OpenRouter Models API](https://openrouter.ai/api/v1/models), confirm prompt and completion pricing are both zero and the needed parameters remain supported, then run the live-provider row in the [demo script](revised-part2-demo-script.md).

## E12 — Revised two-request SQL benchmark

The final verification prompt required a different architecture from the first
implementation: model request one must propose SQL, application validation and
execution must occur between requests, and request two must receive the exact
retrieved records. The earlier one-request/static-query approach was therefore
revised instead of being described as compliant.

The completed pipeline is:

1. request one asks the one configured model for JSON containing either one
   SQL `SELECT` or an `insufficient_data` outcome;
2. FastAPI rejects non-`SELECT`, semicolons, comments, writes, multiple
   statements, unauthorized tables/functions, administrative/extension work,
   excessive SQLite VM work, and oversized results;
3. SQLite compiles the query under a deny-by-default authorizer, then execution
   repeats the authorizer and enforces 50 rows, 20 columns, and 50,000 JSON
   bytes;
4. request two receives the question, validated SQL, and the exact retrieved
   JSON rows;
5. Vue shows the model, proposed SQL, validation/execution decisions, exact
   records, request-two status, and grounded answer.

The validator permits reads only from `saved_hotels`, `saved_hotel_zips`, and
`demo_hotel_nights`. Assignment 1 tables remain unauthorized even for a
`SELECT`. A rejected proposal returns `rejected_query`; it is not executed and
does not reach request two. A successful empty query does reach request two and
can return `no_matches`. An out-of-coverage stay can return
`insufficient_data` before SQL.

## E13 — Fixed JSON sample and repeat commands

The labeled fixture is
`backend/tests/fixtures/revised_part2_fixed_sample.json`. It is explicitly
fixture-only and contains:

- leading-zero ZIP `02108`;
- one qualifying hotel with two ZIP associations;
- a three-night October 10–12 stay whose October 13 checkout is excluded;
- a missing middle night;
- a sold-out included night;
- one night with fewer rooms than requested;
- an out-of-ZIP hotel;
- an exact qualifying total of 67,000 cents for two rooms.

Repeat all focused checks from the repository root:

```bash
cd backend
.venv/bin/python -m pytest -q tests/test_hotel_insights.py
.venv/bin/python scripts/revised_part2_fixture_demo.py
```

The focused run passed **24 tests**. It verifies request ordering, exact records
passed to request two, date and room rules, integer-cent totals, duplicate ZIP
associations, no-match/insufficient outcomes, malformed responses, stage-aware
provider failures, simulated rate limits, forbidden SQL, work/result limits,
credential isolation, and unchanged protected data. The script printed:

```text
FIXTURE ONLY - no live provider was called
Proposed SQL: DELETE FROM saved_hotels
Pipeline status: rejected_query
Validation: rejected
Generated query executed: False
Second model request calls: 0
Protected data unchanged: True
Temporary database removed: True
```

## E14 — Final automated and real-browser observations

Final automated results after the two-request revision:

- backend: **104 passed**, with the same two dependency deprecation warnings;
- frontend: **21 passed**;
- Vite production build: passed with 15 modules transformed;
- no dependency was installed or upgraded.

A genuine Vue/FastAPI browser run used the fixed JSON data in an isolated
temporary SQLite database and a clearly labeled process-local two-response
provider stub. This was not a live OpenRouter call. The browser displayed the
expected Eligible Inn answer, fixture model label, proposed SQL, validation
`passed`, executed-query status, exact retrieved record, request-two status,
leading-zero ZIP, checkout, and 67,000-cent/$670.00 total. A separate `02109`
local lookup showed **Saved locally**, its five stored nights, stored-coordinate
map, and visible Leaflet/OpenStreetMap attribution.

The first real-server pass exposed a genuine issue that in-process tests had
missed: FastAPI could close a synchronous generator dependency's SQLite
connection on a different worker thread, causing `sqlite3.ProgrammingError`.
`connect_database` was revised to use `check_same_thread=False`; request
connections remain individually owned and foreign keys remain enabled. A
cross-thread-close regression test was added. The complete suites passed, and
the corrected real server logged successful `/api/users`, booking-history,
`/api/saved-hotels?zip=02109`, and `/api/hotel-insights` responses without the
thread error. This is the final genuine failed/revised implementation approach
for the AI evidence log.

## E15 — Live-provider status

Safe configuration inspection on October 7, 2026 reported:

```text
OPENROUTER_API_KEY configured: False
OPENROUTER_MODEL: <not configured>
```

Therefore a genuine live two-request OpenRouter success, actual model ID, and
video capture remain **pending**. The fixture model label
`nvidia/class-nemotron:free` is test data and must never be reported as the
course model. Official OpenRouter pages still showed multiple distinct free
Nemotron entries, so no slug was guessed and no paid/automatic fallback was
used.

## E16 — October 8 canonical database and browser checkpoint

This verification used the actual project database and the running production
FastAPI/Vue code, not the fixed fixture. Before mutation, SQLite's online
backup command created the ignored recovery copy
`backend/data/backups/expedia-lite-pre-final-part2-2026-10-08.db`. Its SHA-256
was `5fbc9303ad49f9b452aeecf20471de95db2d138645c73a21e115fd715b676166`, and
`PRAGMA integrity_check` returned `ok`.

| Input/action | Expected result | Observed result | Pass/fail | Correction made |
| --- | --- | --- | --- | --- |
| Search leading-zero ZIP `02108` on October 8, 2026 with no saved rows | `GET /api/saved-hotels?zip=02108` succeeds empty, then and only then `GET /api/hotels?zip=02108` returns current API results. | Uvicorn logged those two requests in that order. Vue displayed **API results**, a 5 km label, 19 live results at observation time, synchronized numbered rows/markers, and visible Leaflet/OpenStreetMap attribution. | Pass | None; live counts are not fixed expectations. |
| Add Beacon Hill Hotel and Bistro and Churchill at Boston View | Each persisted provider hotel gets one `02108` association and exactly five October 10–14 nightly rows; Add disables and Remove appears. | Both live provider identities, names, addresses, and coordinates were saved. Vue immediately showed five `$100.00` / `20` simulated classroom rows for each, disabled Add, and offered Remove. | Pass | None. |
| Repeat `02108` after the two saves | A local hit displays **Saved locally**, rereads SQLite, and prohibits the Part 1 hotel endpoint. | Vue showed two saved hotels. The new Uvicorn log segment contained only `GET /api/saved-hotels?zip=02108`; no `/api/hotels` request followed. | Pass | None. |
| In DB Browser for SQLite, edit Beacon Hill Hotel and Bistro, `2026-10-10`, from 10,000 cents/20 rooms to 15,750 cents/7 rooms and click **Write Changes** | The change commits to the same database used by FastAPI. | DB Browser opened `/Users/jakebutler/Documents/ChatGPT/Expedia-lite/backend/data/expedia-lite.db`; its SQL result reported one row affected. **Write Changes** became enabled, was clicked, and returned to disabled. A separate SQLite read showed `15750` and `7`. | Pass | The first attempted editor value was not inserted because the native text area ignored direct value setting. The SQL editor was refocused and populated using normal paste, then execution and **Write Changes** were visibly rerun successfully. |
| Repeat the same `02108` search without restarting | Current committed values appear; no hardcoded defaults or stale browser/server cache. | Vue displayed Beacon Hill's same October 10 row as **$157.50** and **7**, while the other four nights remained `$100.00` and `20`. | Pass | None. |
| Replay Beacon Hill's actual `POST /api/saved-hotels` provider payload | The save is idempotent: five rows remain and the manual edit is not overwritten. | HTTP 201 returned the existing hotel with five nights; SQL reported `night_count = 5` and `edited_row_preserved = 1`. | Pass | None. |
| Delete Churchill through `DELETE /api/saved-hotels/{place_id}`, then repeat the ZIP search | Only Churchill and its dependent rows disappear; Beacon Hill, its map marker, and edited values remain. | The route returned HTTP 200 with `deleted: true`. Vue then showed **1 saved for this ZIP**, Beacon Hill only, with `$157.50` and `7`. | Pass | The deletion was an API-driven mutation plus genuine browser reread; the separate frontend tests cover the Remove button's exact request contract and failure handling. |
| Fully stop and restart only the FastAPI and Vite processes started for this run; search by pressing Enter | The saved hotel and committed edit survive both process restarts; keyboard search works. | After both restarts, Enter submitted `02108`; Vue again showed **Saved locally**, Beacon Hill, `$157.50`, and `7`. | Pass | None. |
| Compare protected Assignment 1 tables with the pre-checkpoint backup | Local-hotel work does not change `hotels`, `users`, `trips`, `bookings`, `booking_id_sequence`, or `seed_metadata`; database remains healthy. | Bidirectional `EXCEPT` comparisons returned zero differing rows for all six tables. Integrity was `ok`; foreign-key check returned no rows. | Pass | None. |
| Return an `answer` for empty records or `no_matches` for nonempty records; supply contradictory trace flags | Backend and frontend reject internally inconsistent model/API output as an answer-generation/invalid-response failure. | New regression tests passed for both contradictions and for invalid trace state. Focused result: 26 backend tests and 23 frontend tests passed. | Pass | Backend outcome/record consistency and frontend status/trace invariants were added before this checkpoint. |
| Ask a saved-hotel question while OpenRouter configuration is absent | Show an honest provider failure without disturbing hotel search/local data. | Vue displayed **Saved hotel insights unavailable**, “OpenRouter insights service is not configured,” and “The hotel search and local-storage features remain available.” | Pass | This is the real unconfigured-service state, not the required live success. |
| Inspect browser console after the real search, local-storage, restart, and provider-failure checks | No application warning or error entries. | Browser log inspection returned an empty list for warning/error levels. | Pass | None. |

The genuine provider key and exact class model setting are still the only
inputs unavailable to this audit. The live two-request evidence and final
recording cannot be represented as complete until those ignored local settings
exist and the configured model is verified as a free catalog entry.

The complete post-correction check then passed: **106 backend tests**, **23
frontend tests**, the Vite production build with 15 modules transformed, and
the labeled rejected-query fixture. The fixture again reported execution
false, zero second-model calls, protected data unchanged, and temporary
database removal. No dependency was installed or upgraded.
