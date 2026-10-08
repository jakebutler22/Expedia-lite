# Local hotel storage manual demonstration

Use this walkthrough on the Mac after the automated checks pass. Do not open
`backend/.env`, show its contents, or include it in any screenshot or
recording.

Audit note, October 7, 2026: macOS did not detect **DB Browser for SQLite** on
this machine. The audit did not install it because installations require prior
approval. Have the Mac app available before starting the graded walkthrough;
the DB Browser steps and screenshots below remain pending until they are
genuinely completed.

## Record these real values during the demonstration

Do not fill these in from an example. Copy them from the actual browser request
and database rows you create:

- searched ZIP: `________________`
- comparison hotel name: `________________`
- comparison `provider_place_id`: `________________`
- comparison `saved_hotel_id`: `________________`
- comparison date: `________________`
- original rate/rooms: `________________ / ________________`
- edited rate/rooms: `15750 / 7` (`$157.50 / 7` in Vue)
- removal hotel name and IDs: `________________`

## 1. Start Expedia Lite and open the correct database

### Mac Terminal — backend

Open Terminal and run:

```bash
cd "/Users/jakebutler/Documents/ChatGPT/Expedia-lite"
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Expected backend URL: `http://127.0.0.1:8000`.

### Mac Terminal — frontend

Open a second Terminal window and run:

```bash
cd "/Users/jakebutler/Documents/ChatGPT/Expedia-lite"
npm --prefix frontend run dev
```

Open the exact URL printed by Vite, normally `http://127.0.0.1:5173`.

If either Terminal says its port is already in use, do not start a duplicate;
use the already-running project at that URL.

### DB Browser for SQLite

1. Click **Open Database**.
2. Open this exact file:

   ```text
   /Users/jakebutler/Documents/ChatGPT/Expedia-lite/backend/data/expedia-lite.db
   ```

3. On **Database Structure**, confirm `saved_hotels`, `saved_hotel_zips`, and
   `demo_hotel_nights` appear alongside `hotels`, `users`, `trips`, and
   `bookings`. The ZIP association has its own table, so all three local tables
   are required even though the benchmark emphasizes the hotel and nightly
   tables.
4. Open **Execute SQL**, paste this read-only query, and click the play button:

   ```sql
   SELECT name, sql
   FROM sqlite_master
   WHERE type = 'table'
     AND name IN (
       'saved_hotels',
       'saved_hotel_zips',
       'demo_hotel_nights'
     )
   ORDER BY name;
   ```

   Confirm provider identity/name/address/coordinates, the searched-ZIP
   association, the unique hotel/date key, the hotel foreign keys with cascade
   deletion, and defaults `10000` and `20`.
5. Run this baseline query:

   ```sql
   SELECT
     (SELECT COUNT(*) FROM hotels) AS hotels,
     (SELECT COUNT(*) FROM users) AS users,
     (SELECT COUNT(*) FROM trips) AS trips,
     (SELECT COUNT(*) FROM bookings) AS bookings,
     (SELECT next_number FROM booking_id_sequence WHERE singleton = 1)
       AS next_booking_number,
     (SELECT COUNT(*) FROM seed_metadata
       WHERE seed_name = 'initial-csv-data') AS seed_marker;
   ```

   Expected current baseline: `8, 6, 12, 9, 15, 1`. Use **Browse Data** to
   show the actual original IDs and values, not only these counts: H001–H008,
   U001–U006, T001–T012, and the nine current booking rows.

**Capture S1a:** the SQL result with all three new table definitions; the
provider fields, composite keys, `10000`/`20` defaults, and cascading foreign
keys must be legible.
**Capture S1b:** the original table names plus legible original records/IDs.
Use more than one image if the original IDs and booking rows cannot be read in
one frame.

## 2. Save two real API hotels

### Web browser

1. Open Developer Tools, choose **Network**, select **Fetch/XHR**, enable
   **Preserve log**, and clear the list.
2. In Expedia Lite, search ZIP `16802`.
3. Confirm the page says **API results**. Provider counts and hotel names can
   change; record the names actually displayed.
4. Click **Add to Local** on two different hotels. Use the first as the
   comparison hotel and the second as the removal hotel. If the live response
   supplies only one hotel, finish all before/after and repeat-save evidence
   for it before using it for the removal evidence.
5. After each save, confirm **Add to Local** is disabled for that hotel,
   **Remove from Local** appears only for saved hotels, and five rows appear
   for October 10, 11, 12, 13, and 14, 2026.
6. In Network, select the comparison hotel's `POST saved-hotels` request.
   Record its real `searched_zip`, `hotel.place_id`, and hotel name. Right-click
   it and choose **Copy > Copy as cURL**; keep that copied command for step 6.

### DB Browser for SQLite

Click **Refresh** and run:

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

Confirm each hotel has its searched-ZIP association and exactly five rows with
starting values `10000` cents and `20` rooms. Record both real hotel IDs.

**Capture S2:** Vue showing both saved states, disabled Add actions, and the
five-row table.
**Capture S2b:** the DB Browser query showing both ZIP associations and ten
night rows.

## 3. Prove the saved ZIP is local-first

### Web browser

1. Refresh Expedia Lite.
2. In Network, clear the request list.
3. Search the same ZIP again.
4. Confirm the page says **Saved locally**, shows the five stored nights, and
   its markers use the saved coordinates.
5. Confirm Network contains
   `GET /api/saved-hotels?zip=<your ZIP>` with saved results and contains no
   `GET /api/hotels?zip=<your ZIP>`. Map-tile requests are unrelated and may
   still appear.

**Capture S3:** the entered ZIP, **Saved locally**, dated values, and Network
showing the local GET with no Part 1 hotel GET.

## 4. Prove an empty local result falls back

### Web browser

1. Clear Network and search `02108`, provided you did not save a hotel under
   that ZIP. If you did, choose another real five-digit ZIP with no saved
   association.
2. Open the first request and confirm
   `GET /api/saved-hotels?zip=<ZIP>` returned HTTP 200 with `count: 0` and an
   empty `hotels` list.
3. Confirm it is followed by `GET /api/hotels?zip=<ZIP>` and the page says
   **API results**.

**Capture S4:** both requests in order, the empty local response, and the
**API results** label.

## 5. Prove a local failure does not fall back

### Chrome Developer Tools

1. In the Network list from step 3, right-click the exact
   `GET /api/saved-hotels?zip=<saved ZIP>` request and choose **Block request
   URL**. This targets the local lookup you actually observed instead of
   inventing another request pattern.
2. Open DevTools **Network request blocking** from **More tools** and confirm
   that temporary rule is enabled.
3. Clear Network and search that same ZIP.
4. Confirm Expedia Lite shows **Saved hotel lookup unavailable** and says that
   live API fallback was not requested.
5. Confirm no `GET /api/hotels` request appeared.
6. Disable or remove the blocking rule immediately and confirm the next normal
   search works. Do not continue to Add, replay, or Remove while the rule is
   enabled.

**Capture S5:** the temporary block, visible error, and Network with no Part 1
fallback. Do not leave the block enabled.

## 6. Edit a night, reread it, and replay the real save safely

### Web browser — before value

Return to the saved ZIP. Choose the comparison hotel's `2026-10-10` row and
record its actual displayed rate and rooms.

**Capture S6:** comparison hotel, exact date, and original displayed values.

### DB Browser for SQLite — edit and commit

1. Choose **Browse Data** and table `demo_hotel_nights`.
2. Filter to the real comparison `saved_hotel_id` and date `2026-10-10`.
3. Double-click `nightly_rate_cents`, enter `15750`, and press Return.
4. Double-click `rooms_available`, enter `7`, and press Return.
5. Click **Write Changes**. This commit is required.
6. Refresh the data and confirm that exact row still reads `15750` and `7`.

**Capture S7:** the exact hotel/date row showing `15750` and `7` after **Write
Changes**.

### Web browser — fresh reread

Clear Network and repeat the same ZIP search. Confirm the same hotel/date now
shows `$157.50` and `7`, with a fresh local GET and no Part 1 GET.

**Capture S8:** the comparison identity/date, `$157.50`, `7`, **Saved locally**,
and the local Network request.

### Mac Terminal — replay the original request

Open a third Terminal window and paste the exact **Copy as cURL** command saved
from the comparison hotel's original POST. Do not hand-type or invent its
payload. Its route must be:

```text
POST http://127.0.0.1:8000/api/saved-hotels
```

After it succeeds, refresh DB Browser and rerun the saved-hotel join query from
step 2. Confirm the comparison hotel still has exactly five night rows and
`2026-10-10` still reads `15750` and `7`; the replay must not overwrite it.

**Capture S9:** the safe replay response and DB Browser proof of five unchanged
rows. Keep credentials, `.env`, and unrelated headers out of the frame.

## 7. Remove only the second hotel

### Web browser

1. Search the saved ZIP again.
2. Click **Remove from Local** only on the removal hotel.
3. Confirm that hotel disappears from the list and map while the comparison
   hotel remains with `$157.50` and `7`.

If only one hotel was available, do this removal only after S6–S9 are safely
captured, then show the explicit no-saved-hotels state.

### DB Browser for SQLite

Refresh and rerun the join query. Confirm the removal hotel's hotel, ZIP, and
five night rows are gone; the comparison hotel and edited row remain. Recheck
the Assignment 1 tables/records from step 1.

**Capture S10:** the updated Vue list/map and DB rows proving scoped removal
and preserved comparison/original records.

The graded activity is complete only after S7 and S8 prove the DB Browser
**Write Changes** commit was reread by the frontend.
