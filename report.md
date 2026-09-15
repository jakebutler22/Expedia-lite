# Expedia Lite — Part 2

## Repository and commit

[https://github.com/jakebutler22/Expedia-lite](https://github.com/jakebutler22/Expedia-lite)

Repository snapshot: [github.com/jakebutler22/Expedia-lite at the submitted checkpoint](https://github.com/jakebutler22/Expedia-lite/tree/1079eb7b54b00e391e5d0bb16292e565176a9740)

Submitted Part 2 checkpoint: [`1079eb7b54b00e391e5d0bb16292e565176a9740`](https://github.com/jakebutler22/Expedia-lite/commit/1079eb7b54b00e391e5d0bb16292e565176a9740) (`Complete Part 2 CRUD verification evidence and report`). It contains the verified SQLite implementation, complete Vue CRUD interface, tests, project context, report, handoff, and browser evidence. The annotated Git tag `part2-submission` points to this checkpoint. The Part 1 checkpoint remains intact at `77d101ad62bedad9d7dd82fd03b7cf242fbdb17c` under annotated tag `part1-submission`.

## Implementation

Part 2 changes Expedia Lite from a read-only, per-request CSV search into a persistent booking application. All four supplied CSV files now seed SQLite exactly once. A marker written only after the transactional import completes prevents every later startup from replaying starter data, so deleted bookings stay deleted and user-created or cancelled bookings remain unchanged. The schema preserves the supplied hotel, trip, user, and booking text IDs; enforces trip-to-hotel and booking-to-user/trip foreign keys on every connection; and maintains a persistent booking-number sequence so deleted IDs are never reused.

- The **Vue frontend** accepts a partial hotel name or city, preserves the original stay-results columns, loads demo travelers, creates a booking directly from a result row, displays joined booking history, retains cancelled rows with a clear status badge, and requires an in-page confirmation before permanent deletion. It never reads CSV or SQLite files directly.
- The **FastAPI layer** owns HTTP validation and JSON response models, supplies a SQLite connection per request, maps framework-free data errors to appropriate 400/404 responses, and exposes search, user, history, booking-create, booking-read, cancel-update, and delete endpoints.
- The **backend persistence and rules modules** own schema creation, one-time CSV seeding, foreign-key enforcement, SQLite search and CRUD queries, transactional ID allocation, search normalization, SQL-pattern escaping, booking-ID formatting, and stay-price calculations. These data and calculation rules have no FastAPI dependency.

After seeding, no request path reads a CSV file. Search uses one SQLite join and supports trimmed, case-insensitive partial hotel-name matching while retaining trimmed, case-insensitive exact city matching. Cancel and delete are intentionally different operations: cancel updates status and keeps the record; delete removes it permanently.

## Verification

Verification was performed on September 14–15, 2026.

| Action | Expected result | Observed result |
| --- | --- | --- |
| Review every changed file in VS Code Source Control | No request path reads CSV, seeding is marker-gated rather than unconditional, and production booking IDs are not hardcoded. | Opened Source Control and loaded every changed path for file-by-file review. CSV imports and reads occur only in `backend/app/database.py`; `initialize_database` checks `seed_metadata` before `_seed_from_csv`; production IDs come from `booking_id_sequence` and `format_booking_id`. Literal B007/B008 values are confined to tests and recorded verification data. |
| Verify the Git checkpoint and merge history | Reviewed Part 2 work is developed on a feature branch and merged into `main`; the combined application is checked on `main`; the Part 1 checkpoint remains an ancestor of `main` under `part1-submission`. | The reviewed work was committed on `part2-sqlite-crud` at `1079eb7b54b00e391e5d0bb16292e565176a9740`, then fast-forwarded into `main`. On `main` after the merge, the backend suite and frontend production build passed; the browser/restart SmokeTest evidence was captured on the feature branch and was not repeated on `main`. `git merge-base --is-ancestor 77d101ad62bedad9d7dd82fd03b7cf242fbdb17c main` succeeded, and annotated tag `part1-submission` still resolves to that Part 1 commit. |
| Run CHECK → TAKE ACTION → VERIFY for SQLite | Identify the project interpreter, verify `sqlite3`, avoid an unnecessary package installation, and prove file persistence. | CHECK used `/Users/jakebutler/Documents/ChatGPT/Expedia-lite/backend/.venv/bin/python`, Python 3.14.7, and SQLite 3.50.4; the standard-library import passed. TAKE ACTION explicitly skipped installation. VERIFY wrote `(1, 'SQLite persistence verified')` to a temporary database, closed and reopened it, read the same row, and removed the temporary file. |
| Run the backend test suite | Fresh-database seeding, non-reseeding, foreign keys, search, errors, persistent ID allocation, and the complete booking lifecycle pass. | `backend/.venv/bin/python -m pytest backend/tests` collected 26 tests; all 26 passed in 0.24 seconds. Two dependency deprecation warnings were reported. The suite verifies both preferred `query` and deprecated `city` search parameters. |
| Build the Vue frontend | Vite produces a production build without errors. | `npm --prefix frontend run build` transformed 11 modules and completed in 148 milliseconds. |
| Search by hotel name through Vue | Exact and partial hotel-name input returns the matching hotel's stays. | `Harbor Lantern Hotel` returned T001 and T009; partial `Harbor` also displayed those stays. The Vue request used the preferred `query` parameter. |
| Search by city through Vue | Part 1 city behavior remains correct. | `Boston` returned exactly T001, T002, T009, and T010. |
| Search for a missing value through Vue | A clear no-results state appears without a results table. | `Miami` displayed “No hotel stays found for Miami. Try another hotel name or city.” and the search-results region contained no table. |
| Create a booking through Vue | Booking a result for the selected traveler creates a new non-colliding ID and shows it in history. | The original run created B007; the hardening rerun selected U006 and booked T001 as B009 because deleted B008 was not reused. B009 appeared in history as `confirmed`, with joined hotel/trip details and dates. [Created-booking screenshot](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/docs/screenshots/part2-created.jpg). |
| Read booking history through Vue | The selected traveler's bookings show hotel, trip, check-in, check-out, booked-on date, and status; an empty traveler gets a clear message. | U006 initially displayed “Demo Traveler 6 has no bookings.” The hardening rerun showed every required field for retained B007 and new B009. |
| Cancel a booking through Vue | Cancellation retains the row and changes its status to `cancelled`. | Cancelled B009 through its history control. B009 stayed visible with a `cancelled` badge beside retained cancelled B007. [Cancelled-booking screenshot](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/docs/screenshots/part2-cancelled.jpg). |
| Delete a booking through Vue | Inline confirmation permanently removes the chosen test row without deleting retained cancelled bookings. | Created disposable B010, opened its in-page confirmation, and selected **Delete permanently**. B010 disappeared; B007 and B009 remained. Previously deleted B008 also stayed absent. [Deleted-booking screenshot](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/docs/screenshots/part2-deleted.jpg). |
| Refresh the browser | Created, cancelled, and deleted state persists without a process restart. | After a full page refresh, B007 and B009 remained present and `cancelled`, while B008 and B010 remained absent. |
| Fully restart both backend and frontend | Created, cancelled, and deleted state survives a complete application restart. | Stopped only the two processes started for the test, restarted both against the same SQLite file, and reopened U006 history. B007 and B009 remained present and `cancelled`; B008 and B010 did not return. [Full-restart persistence screenshot](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/docs/screenshots/part2-restart-persistence.jpg). |
| Check starter rows after restart | Startup does not duplicate or restore seed records. | SQLite contained 8 hotels, 12 trips, 6 users, and 8 bookings. Each supplied booking B001–B006 occurred once; B007 and B009 were retained additions; the seed-marker count was 1; and the next booking number was 11. |
| Inspect browser warnings, errors, and dialogs | No application console warning/error or JavaScript alert, confirm, or prompt dialog appears. | Browser inspection returned zero warning/error entries and no active JavaScript dialog. Source review found no calls to `alert`, `confirm`, or `prompt`. |

## Project context and next steps

- [Setup and run instructions](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/README.md)
- [Project-specific agent instructions](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/AGENTS.md)
- [Design pipeline](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/docs/design-pipeline.md)
- [Verification procedure and recorded observations](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/docs/verification.md)
- [Selected SQLite-foundation prompt](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/prompts/03-part-2-sqlite-foundation.md)
- [Selected SQLite/API prompt](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/prompts/04-part-2-sqlite-api.md)
- [Selected Vue CRUD prompt](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/prompts/05-part-2-vue-crud.md)
- [Selected verification prompt](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/prompts/06-part-2-verification.md)
- [Current handoff](https://github.com/jakebutler22/Expedia-lite/blob/1079eb7b54b00e391e5d0bb16292e565176a9740/handoffs/current.md)

Part 2's required local SQLite search and booking CRUD workflow is complete. Remaining limitations are appropriate to the classroom scope: demo travelers only, no authentication or authorization, no production deployment controls, no dedicated frontend lint command, and no automated Vue component/end-to-end suite. The next development task is optional frontend verification hardening or the next assigned feature.
