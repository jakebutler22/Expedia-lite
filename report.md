# Expedia Lite — IST 402 Assignment 2.1 Part 1

This Part 1 report was started during the required research and early-design
phase on September 29, 2026, then completed after implementation and
verification. The research, mockup, and initial decisions in sections 1–3 were
recorded **before production implementation of the live hotel search and map**.

## Submission Record

- Repository: [github.com/jakebutler22/Expedia-lite](https://github.com/jakebutler22/Expedia-lite)
- Assessed Part 1 commit: `de43dd9df5c7cc842e9693f29cd43cb85e43507a`
- Submission document: `report.md` (this file)
- Final audit: [docs/part1-final-audit.md](docs/part1-final-audit.md)
- Demo procedure: [docs/part1-demo-script.md](docs/part1-demo-script.md)
- Dated verification: [docs/part1-verification-2026-09-29.md](docs/part1-verification-2026-09-29.md)
- AI evidence: [prompts/07-part-1-live-hotel-search.md](prompts/07-part-1-live-hotel-search.md)

## 1. Research Notes

The focused research is recorded in
[Part 1 live hotel search research](docs/part1-location-research.md). The main
findings that affect implementation are:

- [Geoapify Geocoding](https://apidocs.geoapify.com/docs/geocoding/) supports
  postcode lookup with `type=postcode` and a U.S. country filter. Expedia Lite
  will accept a result only when its returned postcode exactly matches the
  requested five-character ZIP, its country is the United States, and its
  coordinates are valid.
- [Geoapify Places](https://apidocs.geoapify.com/docs/places/) supports a hard
  circle filter and hierarchical categories. The hotel query will use
  `accommodation.hotel`, a 5,000-metre circle around the resolved ZIP, and a
  proximity bias only to order results.
- [Leaflet 1.9.4](https://leafletjs.com/reference.html) supplies keyboard map
  navigation, keyboard-focusable markers, popups, zoom controls, and an
  attribution control. The planned OpenStreetMap layer will follow the
  [OpenStreetMap tile usage policy](https://operations.osmfoundation.org/policies/tiles/),
  including permanently visible attribution.
- The [Google Maps Place Search pattern](https://developers.google.com/maps/documentation/javascript/places-ui-kit/place-search)
  demonstrates a selectable result list connected to markers by one place
  identity. Its success-only example omits the complete validation and failure
  states required here.
- [Airbnb's search-result explanation](https://www.airbnb.com/help/article/39)
  validates showing list and map together for geographic context, but permits
  different results in each view and uses commercial ranking signals. Expedia
  Lite will instead render one identical API result set in both views and will
  not show unreturned prices, ratings, availability, or booking information.

## 2. Early Mockup

[Open the interactive Part 1 early mockup](docs/part1-live-hotel-search-mockup.html).

The mockup was created **before Part 1 implementation**. It is a self-contained
repository artifact with no network calls, API credentials, or claimed hotel
facts. Placeholder labels explicitly identify values that must later come from
the API response.

The mockup shows the ZIP field and Search button, live status/error area,
hotel-result list, Leaflet map area, shared selected-hotel state, loading,
invalid ZIP, unresolved ZIP, zero nearby results, and failed request. Its state
controls make each alternative screen inspectable without changing the real
application.

## 3. Initial Design Decisions

1. Preserve ZIP values as strings and validate exactly five ASCII digits so
   leading zeroes remain intact.
2. Keep the Geoapify key and both provider calls in the backend. The existing
   configuration path must move from project-root `.env` to ignored
   `backend/.env`, with a credential-free `backend/.env.example` added during
   implementation.
3. Expose one FastAPI search workflow: validate ZIP, confirm the exact U.S.
   postcode, use its coordinates as the center, then search only within 5 km.
4. Normalize and return only Geoapify fields that actually exist. Optional
   missing values remain absent.
5. Use Geoapify `place_id` as the shared list/map selection key. One Vue state
   value controls the selected row, marker, and popup.
6. Keep OpenStreetMap/Leaflet attribution visible and make form, result, marker,
   and map controls keyboard usable.
7. Treat ready, loading, results, invalid ZIP, unresolved ZIP, zero results,
   and request failure as distinct UI states.
8. Preserve MVC responsibilities: backend services own provider/configuration
   logic, FastAPI routes own HTTP orchestration, and Vue owns presentation and
   user interaction.

## 4. Implementation

The completed flow keeps the provider boundary entirely in FastAPI. The Vue
client sends a ZIP to `GET /api/hotels`; it never calls Geoapify and never
receives the provider key. `backend/app/geocoding.py` validates exactly five
ASCII digits, requests a U.S. postcode result, and accepts only a response whose
postcode exactly equals the requested string and whose country code is `us`.
The leading-zero ZIP `02108` therefore remains a string throughout the flow.

When the postcode is confirmed, `backend/app/hotel_search.py` passes its
returned coordinate—not a guessed or substitute point—to
`backend/app/places.py`. That service requests `accommodation.hotel` with a hard
5,000-metre circle and proximity bias. It normalizes only provider fields that
are actually present: identity, name, coordinates, address components,
distance, and categories. Records without a provider identity, name, or valid
coordinate are omitted because they cannot support truthful synchronized
display. No price, rating, availability, room, or booking field is fabricated.

The FastAPI route maps invalid format, unresolved postcode, configuration,
timeout, network/HTTP/provider-response failure, empty result, and success to
distinguishable responses. Provider exceptions are converted to fixed safe
messages so neither the API key nor raw provider response details are returned.
The credential is loaded from ignored `backend/.env`; the committed
`backend/.env.example` contains only a placeholder.

Vue uses one returned hotel array for both list rows and Leaflet markers and
one `selectedHotelId` keyed by Geoapify `place_id`. Selecting a keyboard-usable
list button pans to and opens its marker; selecting a keyboard-enabled marker
updates and scrolls to the matching list item. The map frames the confirmed
center and result coordinates, draws the 5 km search circle, keeps the search
center visible even with zero hotels, and leaves Leaflet/OpenStreetMap
attribution visible. Ready, loading, results, invalid, unresolved, no-results,
and request-failure UI states have separate headings and feedback.

MVC responsibilities remain separated: provider/configuration logic lives in
backend service modules, FastAPI owns HTTP status and response-model concerns,
Vue owns presentation and interaction, and the existing SQLite booking models
and data-access flow remain unchanged.

## 5. Verification Evidence

The complete 16-case expected-versus-observed table is recorded in
[the September 29 full verification evidence](docs/part1-verification-2026-09-29.md),
with the reusable procedure retained in [docs/verification.md](docs/verification.md).
On September 29, 2026:

- all 68 backend tests passed in the project virtual environment and the
  Vue/Vite production build completed successfully after the browser-found fix;
- Git ignore checks proved `backend/.env` is ignored while
  `backend/.env.example` is trackable;
- real requests confirmed exact U.S. postcodes `16802` and leading-zero
  `02108`, used 5,000-metre radii, and respectively returned 20 and 19
  normalized provider hotels at the time of testing;
- `1680`, `168021`, and `16A$2` produced invalid responses; `00000` produced
  the unresolved state without a substituted location; and `99999` confirmed
  an exact U.S. location but produced the distinct zero-hotel state;
- temporarily stopping only the backend started for this check produced the
  distinct request-failure state, and restarting it restored successful search.
  A temporary isolated backend with a deliberately invalid test credential
  received a real Geoapify rejection and returned a sanitized HTTP 502 without
  exposing that credential;
- list-to-marker selection worked with Enter. The first Enter test on a map
  marker exposed a real defect: Leaflet opened the popup without updating the
  shared Vue selection. An Enter `keypress` handler was added to use the same
  selection path as a click, and the rerun selected XV Beacon in both views;
- the real credential and its environment-variable name were absent from ten
  checked frontend source/build files and seven sampled frontend/API network
  responses; and
- browser inspection found visible Leaflet/OpenStreetMap attribution and no
  application warning or error entries.

Geoapify data is live, so result ordering and counts can change. The evidence
records the date and observed count rather than treating that count as a fixed
application fact.

## 6. AI Use and Disclosure

AI assistance was used for repository inspection, research synthesis,
implementation, test generation, browser verification, and documentation. The
submitted work was checked against the live application rather than accepted
from generated text alone. The retained
[Part 1 AI evidence log](prompts/07-part-1-live-hotel-search.md) records the
request, affected files, verification, and a legitimate failed approach: the
first Leaflet marker keyboard implementation opened a popup on Enter without
updating Vue selection. The log records the shared-handler correction and the
successful rerun; it is not a fabricated failure added after the fact.

## 7. Demo

The production-ready [Part 1 demo script](docs/part1-demo-script.md) provides a
three-to-four-minute walkthrough and the exact safe macOS recording step if a
video file is requested. The live application and dated verification evidence
are the repository demo artifacts; no prerecorded video is claimed.

1. Start FastAPI and Vue with the commands in [README.md](README.md).
2. Enter `02108` and choose **Search live hotels**. Point out the confirmed ZIP,
   live result count, 5 km circle, numbered rows and markers, and attribution.
3. Select a second hotel in the list; its map popup opens and both views show
   the same selected identity. Then select a different marker and show the list
   selection moving to that hotel.
4. Enter `2108`, `00000`, and `99999` to demonstrate invalid, unresolved, and
   zero-nearby-result states without substituted locations.
5. Explain that visible hotel facts come from the API response and that live
   results intentionally omit price, rating, availability, and booking claims.

Supporting artifacts: [focused research](docs/part1-location-research.md),
[pre-implementation early mockup](docs/part1-live-hotel-search-mockup.html),
[implementation/verification prompt](prompts/07-part-1-live-hotel-search.md),
[full verification evidence](docs/part1-verification-2026-09-29.md), and
[verification procedure](docs/verification.md), plus the
[professor-style final audit](docs/part1-final-audit.md).

## 8. Submission Checklist and Scope Boundary

- Research links, observed strengths/weaknesses, and adopted decisions: present.
- Pre-implementation early mockup: present and explicitly dated in sequence.
- FastAPI/Vue implementation with protected backend configuration: present.
- Expected-versus-observed verification with live ZIPs and date: present.
- Demo script and exact recording procedure: present.
- AI disclosure and evidence, including a real revised approach: present.
- Assessed commit identifier: recorded in the Submission Record above.

This assessed Part 1 work introduces no shortlist, database, authentication,
or booking feature. The repository's pre-existing Part 2 implementation and
its checkpoint were deliberately preserved under `AGENTS.md`; the historical
report below remains only as an appendix and is not part of this Part 1 scope.

---

# Appendix A — Preserved historical Part 2 report

This appendix predates the current Assignment 2.1 Part 1 implementation. It is
retained for repository continuity and is not submitted as new Part 1 work.

## Repository and commit

Repository URL: [https://github.com/jakebutler22/Expedia-lite](https://github.com/jakebutler22/Expedia-lite)

Repository snapshot: [github.com/jakebutler22/Expedia-lite at the submitted checkpoint](https://github.com/jakebutler22/Expedia-lite/tree/8dea025e2b5fc1288899b4847368713158640ed2)

Submitted Part 2 checkpoint: [`8dea025e2b5fc1288899b4847368713158640ed2`](https://github.com/jakebutler22/Expedia-lite/commit/8dea025e2b5fc1288899b4847368713158640ed2) (`Complete Part 2 report URL correction and report`). The immediately following documentation commit on `main` records this hash, and the annotated Git tag `part2-submission` points to this checkpoint. The Part 1 checkpoint remains intact at `77d101ad62bedad9d7dd82fd03b7cf242fbdb17c` under annotated tag `part1-submission`.

The implementation was developed and reviewed on `part2-sqlite-crud`, followed by additive verification hardening on `part2-verification-hardening`. The hardening branch was merged into `main` with explicit merge commit `2b48ff307e6ad6af1573fea0dd006b6c2b153a5e` before the combined application was checked again on `main`. The one-line repository-link correction was then committed on `part2-report-url` and explicitly merged as `c87b7b250f2695891a37eb81ebbc761819a23d1c`.

## Implementation

Part 2 changes Expedia Lite from a read-only, per-request CSV search into a persistent booking application. All four supplied CSV files seed SQLite exactly once. A marker written only after the transactional import completes prevents later startups from replaying starter data, so deleted bookings stay deleted and user-created or cancelled bookings remain unchanged. The schema preserves the supplied hotel, trip, user, and booking text IDs; enforces trip-to-hotel and booking-to-user/trip foreign keys on every connection; and maintains a persistent booking-number sequence so deleted IDs are never reused.

- The **Vue frontend** accepts a partial hotel name or city, preserves the original stay-results columns, loads demo travelers, creates a booking directly from a result row, displays joined booking history, retains cancelled rows with a clear status badge, and requires an in-page confirmation before permanent deletion. It sends the preferred `query` parameter and never reads CSV or SQLite files directly.
- The **FastAPI layer** owns HTTP validation and JSON response models, supplies a SQLite connection per request, maps framework-free data errors to appropriate 400/404 responses, and exposes search, user, history, booking-create, booking-read, cancel-update, and delete endpoints. `/api/stays` prefers `query` while accepting `city` as a deprecated compatibility alias; both describe matching a hotel name or city.
- The **backend persistence and rules modules** own schema creation, one-time CSV seeding, foreign-key enforcement, SQLite search and CRUD queries, transactional ID allocation, search normalization, SQL-pattern escaping, booking-ID formatting, and stay-price calculations. These data and calculation rules have no FastAPI dependency.

After seeding, no request path reads a CSV file. Search uses one SQLite join and supports trimmed, case-insensitive partial hotel-name matching while retaining trimmed, case-insensitive exact city matching. Cancel and delete are intentionally different operations: cancel updates status and keeps the record; delete removes it permanently.

## Verification

Verification was performed on September 14–15, 2026.

| Action | Expected result | Observed result |
| --- | --- | --- |
| Review every changed file in VS Code Source Control | No request path reads CSV, seeding is marker-gated rather than unconditional, and production booking IDs are not hardcoded. | Opened Source Control and loaded every changed path for file-by-file review. CSV imports and reads occur only in `backend/app/database.py`; `initialize_database` checks `seed_metadata` before `_seed_from_csv`; production IDs come from `booking_id_sequence` and `format_booking_id`. Literal booking IDs are confined to tests, seed data, and recorded verification evidence. |
| Verify the Git checkpoint and merge history | Reviewed Part 2 work is developed on feature branches and merged into `main`; the combined application is checked on `main`; the Part 1 checkpoint remains an ancestor of `main` under `part1-submission`. | Part 2 work was reviewed on `part2-sqlite-crud`; verification hardening was committed and pushed on `part2-verification-hardening` at `04438e31af7a183d99be4d112eb8a472a32ffd3f`, then merged with `--no-ff` as `2b48ff307e6ad6af1573fea0dd006b6c2b153a5e`. The one-line report correction was committed and pushed on `part2-report-url` at `bbdfb210e3edb6bf49c03d3be37a07dce2827f2e`, then merged with `--no-ff` as `c87b7b250f2695891a37eb81ebbc761819a23d1c`. The backend suite and production build passed on that merged `main`; the complete automated and browser SmokeTest had already passed on combined `main` after hardening. `git merge-base --is-ancestor 77d101ad62bedad9d7dd82fd03b7cf242fbdb17c main` succeeded, and annotated tag `part1-submission` still resolves to that Part 1 commit. |
| Run CHECK → TAKE ACTION → VERIFY for SQLite | Identify the project interpreter, verify `sqlite3`, avoid an unnecessary package installation, and prove file persistence. | CHECK used `/Users/jakebutler/Documents/ChatGPT/Expedia-lite/backend/.venv/bin/python`, Python 3.14.7, and SQLite 3.50.4; the standard-library import passed. TAKE ACTION explicitly skipped installation. VERIFY wrote `(1, 'SQLite persistence verified')` to a temporary database, closed and reopened it, read the same row, and removed the temporary file. |
| Run the backend test suite on merged `main` | Fresh-database seeding, non-reseeding, foreign keys, both search parameter names, errors, persistent ID allocation, and the complete booking lifecycle pass. | `backend/.venv/bin/python -m pytest backend/tests` collected 26 tests; all 26 passed in 0.26 seconds after the report-URL merge. Two dependency deprecation warnings were reported. `Harbor` returned T001 and T009 through both preferred `query` and deprecated `city`. |
| Build the Vue frontend on merged `main` | Vite produces a production build without errors. | `npm --prefix frontend run build` transformed 11 modules and completed in 166 milliseconds. |
| Search by hotel name through Vue | Exact and partial hotel-name input returns the matching hotel's stays through the preferred `query` parameter. | Exact `Harbor Lantern Hotel` and partial `Harbor` each returned T001 and T009. |
| Search by city through Vue | Part 1 city behavior remains correct. | `Boston` returned exactly T001, T002, T009, and T010. |
| Search for a missing value through Vue | A clear no-results state appears without a results table. | `Miami` displayed “No hotel stays found for Miami. Try another hotel name or city.” and the search-results region contained no table. |
| Create a booking through Vue | Booking a result for the selected traveler creates a new non-colliding ID and shows it in history. | Hardening created B009 for U006, proving deleted B008 was not reused; the merged-main rerun later created B011. Both appeared in history with joined hotel/trip details and dates. [Created-booking screenshot](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/docs/screenshots/part2-created.jpg). |
| Read booking history through Vue | The selected traveler's bookings show hotel, trip, check-in, check-out, booked-on date, and status; a traveler without bookings gets a clear message. | U006 history displayed every required field for retained bookings. After seeded B006 was deleted, U005 displayed “Demo Traveler 5 has no bookings.” |
| Cancel a booking through Vue | Cancellation retains the row and changes its status to `cancelled`. | B009 in the hardening run and B011 on merged `main` stayed visible after cancellation with `cancelled` badges. [Cancelled-booking screenshot](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/docs/screenshots/part2-cancelled.jpg). |
| Delete a booking through Vue | Inline confirmation permanently removes the chosen row without deleting retained cancelled bookings. | Hardening deleted disposable B010; the merged-main rerun deleted disposable B012 and seeded B006 through **Delete permanently**. The deleted rows disappeared while cancelled B007, B009, and B011 remained. [Deleted-booking screenshot](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/docs/screenshots/part2-deleted.jpg). |
| Refresh the browser | Created, cancelled, and deleted state persists without a process restart. | On merged `main`, B011 remained present and `cancelled`; B012 and seeded B006 remained absent; U005 still had no bookings. |
| Fully restart both backend and frontend | Created, cancelled, and deleted state survives a complete application restart, including deletion of a supplied booking. | Stopped only the two processes started for the test, restarted both against the same SQLite file, and reopened U005 and U006 history. B007, B009, and B011 remained `cancelled`; B008, B010, B012, and seeded B006 did not return. [Full-restart persistence screenshot](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/docs/screenshots/part2-restart-persistence.jpg). |
| Check starter rows after restart | Startup does not duplicate or restore seed records. | SQLite contained 8 hotels, 12 trips, 6 users, 8 bookings, and one seed marker. Starter bookings B001–B005 each occurred once; deleted starter B006 remained absent; retained additions were B007, B009, and B011; and the next booking number was 13. |
| Inspect browser warnings, errors, and dialogs | No application console warning/error or JavaScript alert, confirm, or prompt dialog appears. | Browser inspection returned zero warning/error entries and no active JavaScript dialog. Source review found no calls to `alert`, `confirm`, or `prompt`. |
| Inspect the recaptured browser evidence | Each full-page screenshot uses the complete frame without duplicated strips or clipped rows, and booking statuses remain legible. | All four JPEGs are 1280 pixels wide. The restart evidence shows the traveler selector, complete U006 booking history, B007's `CANCELLED` badge, and no B008 row in one frame. |

## Project context and next steps

- [Setup and run instructions](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/README.md)
- [Project-specific agent instructions](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/AGENTS.md)
- [Design pipeline](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/docs/design-pipeline.md)
- [Verification procedure and recorded observations](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/docs/verification.md)
- [Selected SQLite-foundation prompt](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/prompts/03-part-2-sqlite-foundation.md)
- [Selected SQLite/API prompt](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/prompts/04-part-2-sqlite-api.md)
- [Selected Vue CRUD prompt](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/prompts/05-part-2-vue-crud.md)
- [Selected verification prompt](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/prompts/06-part-2-verification.md)
- [Current handoff](https://github.com/jakebutler22/Expedia-lite/blob/8dea025e2b5fc1288899b4847368713158640ed2/handoffs/current.md)

Part 2's required local SQLite search and booking CRUD workflow is complete and hardened. Remaining limitations are appropriate to the classroom scope: demo travelers only, no authentication or authorization, no production deployment controls, no dedicated frontend lint command, and no automated Vue component/end-to-end suite. The next task is the next assigned feature or a separately approved expansion of automated frontend coverage.
