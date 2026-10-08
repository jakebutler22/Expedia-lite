# Local hotel storage verification — October 6, 2026

This record covers the database/backend portion and the later frontend
integration for **Graded In-class Activity 2: Local Hotel Storage and Manual
Verification**. No dependency was installed or upgraded and no CSV seed was
rerun.

## Runtime database and pre-migration baseline

No backend process was running during the initial inspection. The canonical
application default and only project database was:

```text
/Users/jakebutler/Documents/ChatGPT/Expedia-lite/backend/data/expedia-lite.db
```

`backend/app/database.py` derives this path from the backend package location,
and `create_app()` passes it to every request-scoped connection. Before the
additive migration, `PRAGMA integrity_check` returned `ok` and the database
contained:

| Table | Rows | Preserved record baseline |
| --- | ---: | --- |
| `hotels` | 8 | H001–H008 |
| `users` | 6 | U001–U006 |
| `trips` | 12 | T001–T012 |
| `bookings` | 9 | B001 confirmed; B002 cancelled; B003–B005 confirmed; B007, B009, B011, and B013 cancelled |
| `booking_id_sequence` | 1 | `next_number = 15` |
| `seed_metadata` | 1 | `initial-csv-data` |

This baseline is intentionally not the pristine CSV state: it includes retained
Assignment 1 user activity and an absent/deleted B006. The migration preserved
that state exactly.

## Consistent backup

Before migration, SQLite's online backup command created:

```text
backend/data/backups/expedia-lite-pre-local-hotel-storage-2026-10-06.db
```

The backup is ignored by Git. Its integrity check returned `ok`; its six tables
and row counts matched the source, and normalized `.dump` output from source
and backup had the same SHA-256:

```text
758d8acbcb170bb951d1af3aa1a791b0c89e95aff0cfaed90d30018bcf76186d
```

## Additive schema and API

Startup now creates, without dropping or reseeding anything:

- `saved_hotels`: one row per unique provider `place_id`, with provider name,
  address, latitude, and longitude.
- `saved_hotel_zips`: a normalized searched-ZIP association. ZIPs remain text,
  including leading zeroes, and one provider hotel can retain more than one
  searched-ZIP association without duplicate hotel rows.
- `demo_hotel_nights`: one row per saved hotel and date, with a composite
  primary key, database defaults of `10000` cents and `20` rooms, and a
  cascading foreign key to the saved hotel.

The new routes are:

- `GET /api/saved-hotels?zip=<five-digit ZIP>`
- `POST /api/saved-hotels`
- `DELETE /api/saved-hotels/{place_id}`

The save transaction uses fixed dates October 10, 11, 12, 13, and 14, 2026.
Conflict-ignore inserts make saves repeatable without overwriting manually
edited nightly values. Each lookup performs fresh SQL reads through a new
request connection, so committed DB Browser edits appear on the next request.

## Verification

The focused tests use only fresh temporary SQLite databases. Eleven saved-hotel
tests passed
for fixed dates/defaults, leading-zero ZIP storage, repeat-save preservation,
multiple ZIP associations, clear empty results, scoped cascade deletion,
Assignment 1 row preservation, rereading committed external edits, repeated
startup preservation, safe lookup failures, atomic rollback, invalid input,
missing deletion targets, and credential isolation.

The complete backend suite passed: **79 tests**. The frontend production build
passed with 14 modules transformed, and eleven dependency-free Node checks
passed for local-first request ordering, safe failure behavior, fresh reads,
mutation request contracts, exact fixed-date validation, and
stored-money/zero-value formatting.

Starting the documented Uvicorn command applied the migration to the canonical
database. Post-migration `PRAGMA quick_check` returned `ok`, foreign-key checks
returned no violations, every baseline count and booking status remained the
same, and all three new tables started empty. Manual local checks observed:

- `GET /api/saved-hotels?zip=02108`: HTTP 200 with a clear empty result.
- `GET /api/stays?query=Harbor`: HTTP 200 with existing trips T001 and T009.
- `GET /api/health`: HTTP 200 with the safe configuration phrase only.

## Frontend local-first verification

Vue now calls `GET /api/saved-hotels?zip=<ZIP>` before the frozen Part 1
`GET /api/hotels?zip=<ZIP>` contract. A nonempty local response is labeled
**Saved locally** and prevents the Part 1 call. Only a valid, successful empty
local response triggers Part 1 fallback and the **API results** label. Network,
HTTP, and invalid local responses remain errors and never become empty success.

The visible browser confirmed a real empty-local/API-fallback search for ZIP
16802, a successful **Add to Local**, all five October 10–14 nights, and a
repeat search that displayed only the saved record and stored-coordinate map.
After a page refresh, the same explicit search still found the saved record.
A committed database edit changed October 10 to zero cents and zero rooms; the
next search showed `$0.00` and `0` without a backend restart. The existing
`Harbor` search still returned trips T001 and T009. Automated tests separately
cover local lookup failures without calling the provider fallback.

The Part 1 response contract and shared list/map `place_id` selection contract
remain unchanged. Provider results retain the search-center/radius overlay;
saved results fit the map to their stored coordinates.

## October 7 re-verification

The completed integration was rerun on October 7, 2026 without installing or
upgrading dependencies. Automated mutation tests used temporary SQLite
databases. The focused saved-hotel backend suite passed **11 tests**, all
frontend request/formatting suites passed **17 tests**, the full backend suite
passed **91 tests**, and the Vite production build passed with 15 modules
transformed. `git diff --check` also passed.

A separate visible-browser run used the real Vue and FastAPI applications, a
temporary isolated runtime database, and the live Geoapify-backed Part 1 route;
it did not use a mocked hotel provider or change the canonical database. The
browser and backend request log observed:

| Check | Observed result |
| --- | --- |
| Successful empty local lookup | `GET /api/saved-hotels?zip=16802` returned first, then and only then `GET /api/hotels?zip=16802`; both list and map showed **API results**. |
| Add | **Add to Local** issued `POST /api/saved-hotels`, became disabled for that hotel, exposed **Remove from Local**, and displayed all five simulated nightly rows. |
| Refresh persistence/local hit | After refreshing and explicitly searching 16802 again, the request log contained only `GET /api/saved-hotels?zip=16802`; the UI showed **Saved locally** and stored coordinates. |
| Current committed values | An external committed edit changed October 10 to 12,345 cents and zero rooms. Repeating the search without restarting showed `$123.45` and `0`. This exercised the same fresh-read behavior as a DB Browser **Write Changes** commit. |
| Local error | With only the verification backend stopped, the browser showed **Saved hotel lookup unavailable** and explicitly said the live API fallback was not requested. |
| List/map synchronization | Selecting the second saved hotel in the list pressed the matching marker; activating the first marker with Enter pressed the matching list result. |
| Scoped removal | Removing one of two saved hotels left the unrelated hotel, one result, and one marker visible. Removing the last record produced the explicit local-empty state without silently starting Part 1 fallback. |

The canonical database remained untouched at SHA-256
`c43f08bd015ddb73b498d0cff83b3e49ff251fbea4e485ceee0a7b38e5a75622`.
Its integrity check returned `ok`, foreign-key checking returned no rows, and
all three local-hotel tables remained empty after the run. Only processes
started for this verification were stopped, and the temporary database was
removed afterward.

## Final five-benchmark audit — October 7, 2026

| Benchmark | Implementation audit | Required graded evidence |
| --- | --- | --- |
| 1. Schema and preservation | Pass. Required provider fields, searched-ZIP association, composite hotel/date key, cascading relationships, and `10000`/`20` defaults are present. Every row in each of the six original tables compared equal in both directions to the pre-local-storage backup; original-table DDL differences were also zero. | DB Browser schema and original-record screenshots remain pending. |
| 2. Add and retain | Pass. Save creates the five fixed dates, repeat save is idempotent, manual values are not overwritten, refresh/repeat search uses persistent data, and Add disables after success. | Real comparison identity, DB rows, refresh screenshot, and copied-request replay remain pending. |
| 3. Remove | Pass. Deletion is provider-scoped, cascades only related local rows, preserves unrelated/original data, and updates the list/map. Unsaved API rows do not expose Remove. | Final DB Browser and browser removal screenshot remains pending. |
| 4. Local-first lookup | Pass. Local hit suppresses Part 1, empty success falls back, and local failure stops without fallback. Exact labels are present. | Graded DevTools Network screenshots remain pending. |
| 5. Manual reread | Application behavior passes tests and an external committed-edit browser check. | The specifically required DB Browser edit, **Write Changes**, and same-row frontend screenshot remain pending. |

No in-scope production defect was found during this final audit. Documentation
was corrected to use the current 91/11/17 test counts and to distinguish
fixture evidence from genuine browser observations. The DB Browser for SQLite
Mac app was not detectable, and no installation was performed under the
dependency-approval rule.
