# Part 2 verification

Use CHECK → TAKE ACTION → VERIFY for dependencies. Once setup is complete, run AutoLoop with the commands and browser checks below.

## Persistence rules under test

- The four supplied CSV files are immutable, one-time seed sources.
- SQLite is the application's source of truth after the initial seed completes; request paths do not read CSV files.
- A cancelled booking remains stored and visible with status `cancelled`.
- A deleted booking is permanently absent and must not be restored by a refresh, restart, or another seed check.
- Reopening the same database must retain new bookings without duplicating the supplied 8 hotels, 12 trips, 6 users, and 6 starter bookings.

## Automated checks

From the project root:

```bash
backend/.venv/bin/python -m pytest backend/tests
npm --prefix frontend run build
```

Expected: all backend tests pass and Vite completes a production build without errors.

## SQLite environment verification

Re-verified during the Part 2 submission session on September 14, 2026 using `/Users/jakebutler/Documents/ChatGPT/Expedia-lite/backend/.venv/bin/python`.

```text
interpreter=/Users/jakebutler/Documents/ChatGPT/Expedia-lite/backend/.venv/bin/python
python=3.14.7
sqlite=3.50.4
sqlite3_import=passed
installation=skipped (standard-library import succeeded)
round_trip_row=(1, 'SQLite persistence verified')
temporary_database_removed=True
```

CHECK identified the project interpreter and successfully imported `sqlite3`. TAKE ACTION skipped installation because SQLite support is provided by that interpreter's standard library. VERIFY created a temporary database outside the repository, inserted and committed one row, closed and reopened the file, read the same row, and removed the temporary database.

## Browser SmokeTest

Run the following without editing code or dependencies. Start fresh backend and frontend processes specifically for this test, record their process IDs, and stop only those processes.

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Run the backend test suite and frontend production build. | Both commands pass. |
| 2 | Search an exact or partial hotel name from the supplied data. | The matching hotel's offered stays appear. |
| 3 | Search `Boston`. | Exactly T001, T002, T009, and T010 appear. |
| 4 | Search a value absent from the supplied data, such as `Miami`. | A clear no-results message appears and the results table is absent. |
| 5 | Select a demo traveler, create a new booking from a search result, and inspect history. | The API-assigned booking ID appears in that traveler's history. |
| 6 | Cancel the new booking using its in-page control. | The row remains visible and its status changes to `cancelled`. |
| 7 | Create or select a separate test booking, use the in-page delete confirmation, and delete it. | The test booking disappears entirely from history. |
| 8 | Refresh the browser. | The new booking remains cancelled and the deleted booking remains absent. |
| 9 | Fully stop and restart both test-started applications, then reopen history. | The new booking is present and cancelled; the deleted booking has not returned. |
| 10 | Check database counts after restart. | Starter data is not duplicated: 8 hotels, 12 trips, 6 users, with bookings equal to the six starter rows plus retained test-created rows minus test-deleted rows. |
| 11 | Inspect the browser console. | No application warnings or errors appear. |

Capture full-page JPEG screenshots after steps 5, 6, 7, and 9. Save them in `docs/screenshots/` as:

- `part2-created.jpg`
- `part2-cancelled.jpg`
- `part2-deleted.jpg`
- `part2-restart-persistence.jpg`

Every booking row and the status column must be legible in each screenshot. The restart screenshot is the persistence evidence.

## Recorded Part 2 observations

Verified on September 14, 2026 against `backend/data/expedia-lite.db` using backend process 36197 and frontend process 36217, followed by a full restart as backend process 37926 and a new Vite process. Only those SmokeTest processes were stopped.

| Check | Observed result | Status |
| --- | --- | --- |
| VS Code Source Control review | Opened the Expedia Lite workspace and Source Control, loaded every changed file, and reviewed the complete Git diff. Production CSV reads occur only in `backend/app/database.py`; `initialize_database` checks `seed_metadata` before calling `_seed_from_csv`; production booking IDs come from `booking_id_sequence` and `format_booking_id`, with literal booking IDs confined to tests and seed data. | Pass |
| Backend test suite | `backend/.venv/bin/python -m pytest backend/tests` collected 23 tests; all 23 passed in 0.17 seconds. Two existing dependency deprecation warnings were reported. | Pass |
| Frontend production build | `npm --prefix frontend run build` transformed 11 modules and completed in 140 milliseconds. | Pass |
| Hotel-name search | Searching exact hotel name `Harbor Lantern Hotel` returned T001 and T009. | Pass |
| City search | Searching `Boston` returned exactly T001, T002, T009, and T010. | Pass |
| No-results state | Searching `Miami` displayed “No hotel stays found for Miami. Try another hotel name or city.” and the search-results region contained no table. | Pass |
| Browser create | Selected U006 and booked T001 through the results table. New booking B007 appeared in history with status `confirmed`. | Pass |
| Browser cancel | Cancelled B007 through its history control. B007 stayed visible and changed to `cancelled`. | Pass |
| Browser delete | Created disposable booking B008, opened its in-page confirmation, and selected **Delete permanently**. B008 disappeared while B007 remained. | Pass |
| Browser refresh | After a full page refresh, B007 remained visible and cancelled; B008 remained absent. | Pass |
| Full process restart | Fully stopped and restarted both test-started applications. B007 remained visible and cancelled; B008 did not return. | Pass |
| Seed and row counts after restart | SQLite contained 8 hotels, 12 trips, 6 users, and 7 bookings. Each supplied booking B001–B006 occurred exactly once, B007 was the one retained addition, the seed marker count was 1, and the next booking number remained 9. | Pass |
| Browser console and dialogs | No application warning or error entries and no active JavaScript dialog were present. | Pass |

Evidence: [created booking](screenshots/part2-created.jpg), [cancelled booking](screenshots/part2-cancelled.jpg), [deleted test booking](screenshots/part2-deleted.jpg), and [persistence after full restart](screenshots/part2-restart-persistence.jpg).

### Verification-hardening rerun

Re-verified on September 15, 2026 on branch `part2-verification-hardening`. The first backend/Vite pair was fully stopped, both applications were restarted against the same SQLite file, and the restarted pair was also stopped after verification. No unrelated process was stopped.

| Check | Observed result | Status |
| --- | --- | --- |
| Backend test suite | `backend/.venv/bin/python -m pytest backend/tests` collected 26 tests; all 26 passed in 0.24 seconds. The suite includes `query` and deprecated `city` parameter coverage, with `Harbor` returning T001 and T009 for each. | Pass |
| Frontend production build | `npm --prefix frontend run build` transformed 11 modules and completed in 148 milliseconds. | Pass |
| Browser searches | Partial hotel name `Harbor` returned T001 and T009; city `Boston` returned exactly T001, T002, T009, and T010; `Miami` showed the clear no-results message with no results table. | Pass |
| Browser create and cancel | Created B009 for U006 through the results table, then cancelled it through history. B009 remained visible with status `cancelled`; previously retained B007 also remained `cancelled`. | Pass |
| Browser delete | Created disposable B010, used the in-page **Delete permanently** control, and confirmed B010 disappeared from history. | Pass |
| Browser refresh | B007 and B009 remained visible and `cancelled`; deleted B008 and B010 remained absent. | Pass |
| Full process restart | Fully stopped and restarted both test-started applications. B007 and B009 remained visible and `cancelled`; B008 and B010 did not return. | Pass |
| Seed and row counts after restart | SQLite contained 8 hotels, 12 trips, 6 users, and 8 bookings. Each supplied booking B001–B006 occurred exactly once, the seed marker count was 1, and the next booking number was 11. | Pass |
| Browser console and dialogs | No warning or error entries and no active JavaScript dialog were present. | Pass |

The four JPEGs above were recaptured from clean 1280-pixel-wide browser frames. They show the complete page without the prior duplicated footer or clipped partial row; the restart image keeps the traveler selector, full booking-history rows, and status badges legible together.

## Manual source review

Before committing, inspect every changed file in VS Code Source Control. Confirm only the one-time database initializer reads CSV files; all application reads and writes use SQLite; calculation and data rules remain independent of FastAPI; the frontend performs search, create, history, cancel, and delete through FastAPI; and cancel and delete remain visibly and behaviorally distinct.

## Historical Part 1 observations

Verified on September 9-10, 2026 with Python 3.14.7, FastAPI 0.141.1, Uvicorn 0.52.4, Node 24.12.0, npm 11.6.2, Vue 3.5.42, and Vite 8.2.2.

| Check | Observed result | Status |
| --- | --- | --- |
| Manual VS Code Source Control review | Completed a file-by-file Source Control review. Confirmed `backend/app/search.py` is the only layer reading CSVs and joins hotels to trips on `hotel_id`; `frontend/src/App.vue` calls the FastAPI endpoint and supplies headings for all eight table columns; no SQLite or booking CRUD code is present. | Pass |
| CHECK → TAKE ACTION → VERIFY dependency cycle | CHECK used Python 3.14.7 at `backend/.venv/bin/python`, Node v24.12.0, and npm 11.6.2; FastAPI/Uvicorn and the project-local Vue packages required installation. TAKE ACTION installed `backend/requirements.txt` into `backend/.venv` and the frontend packages into `frontend/node_modules`. VERIFY reran the version commands and successfully imported FastAPI 0.141.1 and Uvicorn 0.52.4 from the project interpreter. | Pass |
| Backend pytest suite | 5 tests passed. | Pass |
| Frontend production build | Vite transformed 11 modules and completed the build. | Pass |
| Initial page | Heading, labeled city input, Search button, and guidance were visible. | Pass |
| `Boston` | Four rows appeared: T001, T002, T009, and T010, with joined hotel details and calculated prices. | Pass |
| `boston` | The same four trip IDs appeared. | Pass |
| `Miami` | “No hotel stays found for Miami. Try another city.” appeared; zero tables remained. | Pass |
| Whitespace-only city | “Enter a city to search for available stays.” appeared; zero tables remained. | Pass |
| Browser console | No warning or error entries were recorded. | Pass |

Evidence: [Boston results](https://github.com/jakebutler22/Expedia-lite/blob/9cece9b63a73802ff7921acb068bd3fddc62905a/docs/screenshots/part1-boston-results.jpg) and [Miami no-results state](https://github.com/jakebutler22/Expedia-lite/blob/9cece9b63a73802ff7921acb068bd3fddc62905a/docs/screenshots/part1-miami-no-results.jpg).
