# Revised Part 2 recorded-demonstration record

The completed recording is
[docs/videos/expedia-lite-revised-part2-demo.mp4](videos/expedia-lite-revised-part2-demo.mp4).
It used the user-approved current zero-price catalog entry
`nvidia/nemotron-3.5-lightning:free` on October 8, 2026. The short-lived key
remained only in ignored `backend/.env`; the recording does not show that file,
the key, authorization headers, or Terminal environment output. The exact
classroom model slug was unavailable and is not claimed.

DB Browser for SQLite 3.13.1 was available on October 8. The audit genuinely
opened the canonical database, changed Beacon Hill Hotel and Bistro's October
10 values to 15,750 cents and 7 rooms, clicked **Write Changes**, and observed
Vue reread `$157.50` and `7` before and after a full process restart. The final
recording should repeat or clearly show this already-verified checkpoint.

## Mac Terminal — start and precheck

Open Terminal window 1:

```bash
cd "/Users/jakebutler/Documents/ChatGPT/Expedia-lite"
backend/.venv/bin/python -m pytest -q backend/tests
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Open Terminal window 2:

```bash
cd "/Users/jakebutler/Documents/ChatGPT/Expedia-lite"
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173`. FastAPI is at `http://127.0.0.1:8000`, and its
documentation is at `http://127.0.0.1:8000/docs`.

For the clearly labeled rejected-query fixture, use Terminal window 3:

```bash
cd "/Users/jakebutler/Documents/ChatGPT/Expedia-lite/backend"
.venv/bin/python scripts/revised_part2_fixture_demo.py
```

This fixture uses a temporary database, calls no live provider, and deletes
itself. It must print `rejected_query`, `Generated query executed: False`,
`Second model request calls: 0`, and `Protected data unchanged: True`.

## DB Browser for SQLite — open the actual database

1. Choose **Open Database**.
2. Open exactly:

   ```text
   /Users/jakebutler/Documents/ChatGPT/Expedia-lite/backend/data/expedia-lite.db
   ```

3. Keep **Database Structure**, **Browse Data**, and **Execute SQL** available.
4. Do not open `backend/.env` during recording.

## Web browser — recording sequence

### 1. Search/map and local-storage foundation

1. Open DevTools → **Network**, select **Fetch/XHR**, enable **Preserve log**,
   and clear the list.
2. Search a valid ZIP with current API results, such as `16802`. Record the ZIP
   actually used and the observation date; do not promise a fixed result count.
3. Show **API results**, the 5 km map, visible attribution, and synchronized
   list/marker selection.
4. Save two different hotels with **Add to Local** if available. Use one as the
   comparison hotel and the other for later removal. Show Add disabled, Remove
   visible, and the five October 10–14 rows.
5. Refresh and search the same ZIP. Show **Saved locally** and Network containing
   `GET /api/saved-hotels?zip=<ZIP>` with no `GET /api/hotels?zip=<ZIP>`.

Evidence target: ZIP/date, list/map synchronization, local/API label, five
stored nights, and request order are all legible.

### 2. Successful live two-request RAG trace

Ask a precise question using the real saved ZIP, dates, and room count, for
example:

> Which saved hotels for ZIP 16802 can provide 2 rooms from check-in 2026-10-10 through checkout 2026-10-13, and what is the simulated total cost?

Show, in this order:

1. loading state;
2. **SQL-generation model request** and the actual configured model ID;
3. proposed SQL;
4. validation status `passed`;
5. bounded query execution;
6. exact retrieved records;
7. **Grounded-answer model request** marked sent;
8. final answer.

State the model ID and recording date aloud. The completed run is live
OpenRouter evidence because the configured provider genuinely returned both
responses; the trace records the actual returned model identity.

Evidence target: the whole on-screen trace, exact model ID, retrieved rows, and
answer. Network will show the browser's single `POST /api/hotel-insights`; the
two provider stages are backend-only and are exposed through the safe trace.

### 3. Compare the answer with SQLite

In DB Browser → **Execute SQL**, run:

```sql
SELECT
  h.saved_hotel_id,
  h.provider_place_id,
  h.hotel_name,
  z.searched_zip,
  n.night_date,
  n.nightly_rate_cents,
  n.rooms_available
FROM saved_hotels AS h
JOIN saved_hotel_zips AS z USING (saved_hotel_id)
JOIN demo_hotel_nights AS n USING (saved_hotel_id)
ORDER BY h.saved_hotel_id, z.searched_zip, n.night_date;
```

Compare the exact hotel identity, included dates, minimum availability, and
integer-cent total with the retrieved-record table and answer. Point out that
check-in is included and checkout is excluded, and all values are simulated
classroom data.

Evidence target: database rows and corresponding browser record/answer can be
read without exposing credentials.

### 4. No-match and insufficient-data cases

1. Ask for more rooms than are available on at least one stored night. A valid
   empty query must reach request two and display **No saved hotel matches**.
2. Ask for a November 2026 stay. Because it is outside October 10–14 coverage,
   show **Insufficient saved data**, no SQL execution, and no second request.

Evidence target: distinct states and their trace decisions.

### 5. Rejected-query fixture

Run the fixture command from Terminal window 3 and record its complete labeled
output. Explain that the attempted SQL is `DELETE FROM saved_hotels`, the
validator rejects it before execution, request two is never called, every
protected table is identical before/after, and the temporary fixture database
is removed.

Evidence target: all six fixture output lines, especially the fixture-only
label and unchanged-data result. Do not present it as a live model failure.

### 6. Required DB Browser edit and reread

1. Before editing, capture the comparison hotel's exact `saved_hotel_id`,
   `provider_place_id`, date `2026-10-10`, displayed rate, and rooms.
2. In DB Browser → **Browse Data** → `demo_hotel_nights`, filter to that
   `saved_hotel_id` and `night_date`.
3. Change `nightly_rate_cents` to `15750` and `rooms_available` to `7`.
4. Click **Write Changes**. This click is required.
5. Repeat the same ZIP search. Show the same row as `$157.50` and `7`.
6. Repeat the same chatbot question. Show a fresh local GET, new SQL execution,
   updated retrieved record, and updated answer/total without restarting.

Evidence target: before row, committed DB Browser row, Vue reread, and chatbot
reread all identify the same hotel/date.

### 7. Persistence, removal, and preservation

1. Refresh the browser, then stop and restart only the two project processes.
2. Repeat the ZIP search and show the edited comparison values still present.
3. Remove only the second saved hotel. Show its list item/marker disappearing
   while the comparison hotel and its edited values remain.
4. Refresh DB Browser and show the removed hotel's ZIP/night rows gone.
5. Show the original `hotels`, `users`, `trips`, and `bookings` tables still
   present. Do not delete the comparison hotel until all evidence is secured.

Evidence target: restart persistence, scoped removal, remaining comparison row,
and preserved Assignment 1 data.

## Recording/upload status

- Local recording file:
  `docs/videos/expedia-lite-revised-part2-demo.mp4`
- Accessible video URL:
  <https://github.com/jakebutler22/Expedia-lite/raw/refs/heads/main/docs/videos/expedia-lite-revised-part2-demo.mp4>
- Rejected-query safety supplement:
  <https://github.com/jakebutler22/Expedia-lite/raw/refs/heads/main/docs/videos/expedia-lite-rejected-query-supplement.mp4>
- Live model ID/date: `nvidia/nemotron-3.5-lightning:free`, October 8, 2026
- Recording contents: local-first `02108` result; stored `$157.50`/7-room
  value; synchronized list/map with visible attribution; complete successful
  request-one → validated SQL → exact row → request-two → `$715.00` answer;
  and a distinct passed/executed successful-empty **No saved hotel matches**
  case.
- File verification: H.264, ISO MP4 v2, 1280 × 828, 104.88 seconds,
  approximately 51 MB; SHA-256
  `397e01c83f64eb4181d7a8453afef20ae5b4266982631c4163d6ff197ad641de`.
- Supplement verification: H.264, ISO MP4 v2, 1280 × 828, 14.88 seconds,
  approximately 10.4 MB; SHA-256
  `6cbab6c396d0bd33c33059ab3d5bb33a29736fe92e8d6945d724fbbab5047a15`.
- DB Browser Write Changes checkpoint: **VERIFIED October 8, 2026** using
  Beacon Hill Hotel and Bistro, `2026-10-10`, 10,000 cents/20 rooms → 15,750
  cents/7 rooms; Vue displayed `$157.50`/`7` without restart and after restart.

The report and dated evidence log contain the additional expected-versus-
observed insufficient-data, rejected-query, DB Browser, restart, removal, and
preservation checks. The public video link is verified after the final push so
the instructor does not need a separate access request.
