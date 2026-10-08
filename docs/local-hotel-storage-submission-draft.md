# Local hotel storage submission draft

Replace bracketed text only after the named screenshot or recording exists.
Do not claim an in-class demonstration unless it actually happened. Keep API
keys and `.env` contents out of every image and recording.

## Demonstration record

- saved ZIP: **[PENDING actual ZIP]**
- comparison hotel: **[PENDING actual name]**
- provider identity: **[PENDING actual `provider_place_id`]**
- local identity: **[PENDING actual `saved_hotel_id`]**
- comparison date: **[PENDING actual date; use 2026-10-10 if practical]**
- before: **[PENDING actual cents/displayed rate and rooms]**
- after: **15750 cents / $157.50 and 7 rooms [PENDING DB Browser and Vue confirmation]**
- removal hotel: **[PENDING actual name and IDs]**

## Benchmark 1 — Schema and preservation

**Expected:** The local tables preserve provider details and searched ZIPs,
enforce one row per hotel/date, default to 10000 cents and 20 rooms, and relate
night/ZIP rows to their hotel without changing Assignment 1 data.
**Observed:** The audit found the required schema, healthy integrity and foreign
keys, and zero value differences in either direction for every row in the six
original tables versus the pre-local-storage backup. **[PENDING DB Browser
view of the definitions and original records.]**
**Evidence:** **[PENDING S1a and S1b]**
**Status:** Automated audit passed; required DB Browser evidence pending.

## Benchmark 2 — Add and retain

**Expected:** Add saves one API hotel, its ZIP, and exactly five October 10–14
rows; Add becomes disabled, refresh retains the hotel, and replaying the same
save does not duplicate rows or overwrite a manual edit.
**Observed:** Temporary-database tests verified the exact rows, defaults,
idempotence, and edit preservation. In a separate real-browser run against an
isolated database on October 7, ZIP 16802 returned live API hotels; Add became
disabled, Remove appeared, five dated rows appeared, and refresh plus the same
ZIP search returned **Saved locally**. **[PENDING the graded comparison hotel,
IDs, DB Browser rows, and copied-request replay.]**
**Evidence:** **[PENDING S2, S2b, S3, and S9]**
**Status:** Tests and tool-assisted browser check passed; graded manual evidence
pending.

## Benchmark 3 — Remove

**Expected:** Remove deletes only the chosen saved hotel and its related ZIP
and nightly rows, preserves unrelated/original records, and updates the list
and map. Unsaved API hotels do not show Remove.
**Observed:** Temporary-database tests verified scoped cascading deletion and
exact preservation of all Assignment 1 values. The October 7 isolated
real-browser run saved two live API hotels, removed one, and left one result,
one matching marker, and one Remove action. **[PENDING removal of the graded
second hotel and DB Browser confirmation.]**
**Evidence:** **[PENDING S10]**
**Status:** Tests and tool-assisted browser check passed; graded manual evidence
pending.

## Benchmark 4 — Local-first lookup

**Expected:** A local hit shows **Saved locally** without a Part 1 hotel call;
a successful empty lookup calls Part 1 and shows **API results**; a failed
local request shows an error without fallback.
**Observed:** In the October 7 isolated real-browser run, ZIP 16802 first logged
`GET /api/saved-hotels?zip=16802` followed by `GET /api/hotels?zip=16802` and
showed **API results**. After saving and refreshing, the same search logged
only the local GET and showed **Saved locally**. Stopping only the verification
backend produced **Saved hotel lookup unavailable** and no fallback result.
Request-level tests separately cover HTTP, network, and malformed local
responses. **[PENDING graded Network-panel screenshots.]**
**Evidence:** **[PENDING S3, S4, and S5]**
**Status:** All paths observed or tested; required captured Network evidence
pending.

## Benchmark 5 — Manual DB Browser reread

**Expected:** After editing both values and clicking **Write Changes**, the
next search rereads the same committed hotel/date and displays the new values
without a restart or reseed.
**Observed:** Tests verify fresh committed reads. In the October 7 isolated
tool-assisted browser run, an external SQLite commit changed a saved ZIP 16802
hotel's 2026-10-10 row from 10000 cents/20 rooms to 12345 cents/0 rooms; the
next search showed `$123.45` and `0` without restarting. That was not DB Browser
and does not replace this benchmark. **[PENDING the graded DB Browser edit to
15750/7 and the matching Vue reread.]**
**Evidence:** **[PENDING S6, S7, and S8]**
**Status:** Application behavior verified; required DB Browser demonstration
pending.

## Automated checks — fixture evidence only

- Focused saved-hotel backend suite: **11 passed**.
- Full backend suite: **91 passed**, with two dependency deprecation warnings.
- Frontend request/format checks: **17 passed**.
- Frontend production build: **passed**, 15 modules transformed.
- Canonical SQLite integrity: `ok`; foreign-key check returned no violations.
- Exact preservation comparison: zero rows differed in either direction and
  zero original-table DDL definitions differed across `hotels`, `users`,
  `trips`, `bookings`, `booking_id_sequence`, and `seed_metadata` versus the
  pre-local-storage backup.

These checks used isolated fixtures for mutations. The October 7 observations
described above used the real Vue/FastAPI application, an isolated runtime
database, and live Geoapify results. Neither category replaces the required DB
Browser screenshots.

## Remaining manual steps

1. Make DB Browser for SQLite available on the Mac; the October 7 audit did not
   detect it and did not install it.
2. Capture S1a–S1b for the schema and preserved original records.
3. Save the real comparison/removal hotels and record their ZIP, names, and
   IDs; capture S2–S2b.
4. Capture local-hit, empty-fallback, and blocked-local-failure Network evidence
   as S3–S5.
5. Capture the comparison row before, commit `15750` and `7` with **Write
   Changes**, and capture the same frontend row after reread as S6–S8.
6. Replay the copied real POST and capture the unchanged five rows as S9.
7. Remove the second hotel and capture scoped deletion as S10.

The graded activity ends only after the DB Browser **Write Changes** commit and
the matching frontend reread are captured.
