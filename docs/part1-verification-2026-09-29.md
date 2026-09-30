# Assignment 2.1 Part 1 full verification — September 29, 2026

This pass exercised the running FastAPI service at `http://127.0.0.1:8000`
and the running Vue application at `http://127.0.0.1:5173`. It used the real
configured Geoapify service for valid, unresolved, successful-result, and
zero-result searches. Live provider counts are observations from this date,
not fixed application expectations.

No dependency was installed. The already-installed `leaflet@1.9.4`, FastAPI,
HTTPX, pytest, and python-dotenv environments were used as-is.

## Expected versus observed

| # | Input/action | Expected result | Observed result | Pass/fail | Correction made if necessary |
| --- | --- | --- | --- | --- | --- |
| 1 | **2026-09-29 live search:** submit ZIP `16802` in Vue and call `/api/hotels?zip=16802`. | Geoapify must confirm the exact U.S. postcode and the application must show a successful provider-backed result state centered on the returned coordinate. | API returned HTTP 200 with postcode `16802`, country `us`, radius `5000`, and 20 hotels. Vue showed “20 hotels near ZIP 16802,” centered on State College, with the same 20 list entries and markers. The count is dated provider evidence, not a fixed assertion. | Pass | None. |
| 2 | **2026-09-29 live search:** submit leading-zero ZIP `02108` using Enter. | The leading zero must remain intact; the confirmed response and UI must identify `02108`, not `2108` or a substitute. | API returned HTTP 200 with exact postcode `02108`, country `us`, radius `5000`, and 19 hotels. Vue showed “19 hotels near ZIP 02108” centered on Boston. | Pass | None. |
| 3 | Enter `1680` and submit; also call the API directly. | Client must show invalid input and FastAPI must return HTTP 400 without calling Geoapify. | Vue showed **Invalid ZIP** with the five-digit guidance. API returned HTTP 400 with “Enter a five-digit U.S. ZIP code.” | Pass | None. |
| 4 | Enter `168021` and submit; also call the API directly. | Six digits must not be accepted. | Vue retained the distinct **Invalid ZIP** state. API returned HTTP 400 with the same safe validation message. | Pass | None. |
| 5 | Enter `16A$2` and submit; also call the API directly. | Letters and symbols must be rejected as invalid input. | Vue showed **Invalid ZIP**. API returned HTTP 400; no provider detail or key appeared. | Pass | None. |
| 6 | **2026-09-29 live search:** submit `00000`. | If Geoapify cannot establish the exact requested U.S. postcode, return unresolved; never substitute another postcode or location. | API returned HTTP 404, “ZIP code 00000 could not be resolved.” Vue showed the distinct **ZIP not resolved** state and no result list/map substitution. | Pass | None. |
| 7 | **2026-09-29 live search:** inspect successful `02108` response and rendered results. | Return only normalized provider data; list and map must be generated from the exact same array and omit invented commercial data. | API `count` and `hotels.length` were both 19. Vue exposed the same 19 named list controls and 19 named markers. Displayed names, addresses, coordinates, and distances matched response data; the live section showed no price, rating, availability, room, or booking claims. | Pass | None. |
| 8 | **2026-09-29 live search:** submit `99999`. | If the exact U.S. postcode resolves but Places returns no hotels, show a distinct zero-result state while retaining the confirmed center and map. | API returned HTTP 200 with exact postcode `99999`, radius `5000`, `count: 0`, and an empty hotel array. Vue showed **No nearby hotels**, an empty list explanation, the confirmed-center map, and visible controls/attribution. | Pass | None. |
| 9 | With `02108` results, activate the Churchill at Boston View list result using Enter. | The list item and matching marker must become the same selected hotel and its popup should open. | The Churchill list control changed to selected, its marker changed to selected, and the Churchill popup opened. | Pass | None. |
| 10 | With `02108` results, activate the XV Beacon map marker using Enter. | The marker and matching list item must become the same selected hotel. | Initial verification exposed a defect: Leaflet opened the popup on Enter but the shared Vue selection remained on the prior hotel. After correction, the rerun changed both XV Beacon controls to selected and opened its popup. | Pass after correction | Added an Enter `keypress` handler to each Leaflet marker so keyboard activation invokes the same `selectLiveHotel` path as pointer clicks. Rebuilt and reran successfully. |
| 11 | **2026-09-29 live search:** submit `02108` and inspect the in-flight UI. | A distinct loading state must appear and prevent duplicate submission until the response completes. | Input and submit button became disabled, button text changed to “Searching…,” and the status region showed “Searching ZIP 02108…” before results replaced it. | Pass | None. |
| 12 | Stop only the test-started FastAPI process, submit `02108`, then restart and retry. Separately start a temporary backend on port 8001 with a deliberately invalid test credential and call its hotel route. | Vue must show a distinct safe failed-request state and recover. A real Geoapify rejection must map to a sanitized service error without returning the rejected credential. | While FastAPI was stopped, Vue showed **Live search unavailable** with safe retry guidance. After restart, the same search succeeded. The isolated invalid-credential backend received the real provider rejection and returned HTTP 502, “Geoapify hotel search failed,” with `invalid_key_exposed: false`; that temporary backend was then stopped. | Pass | None in this pass. An earlier development check had already replaced the raw browser “Failed to fetch” text with the current stable message. |
| 13 | Compare the configured key against frontend source/build files and sampled network responses: `/`, `/src/main.js`, `/src/App.vue`, `/src/styles.css`, `/api/health`, `/openapi.json`, and `/api/hotels?zip=02108`. | Neither the credential nor the backend environment variable name may be exposed to the browser or API consumer. | Ten frontend source/build files and all seven sampled responses contained neither the real key nor `GEOAPIFY_API_KEY`. Every tested hotel response also reported `key_exposed: false`. Browser requests target FastAPI; Geoapify calls remain in backend service modules. | Pass | None. |
| 14 | Run `git check-ignore -v backend/.env`, check tracking status, and check `backend/.env.example`. | Real `.env` must be ignored/untracked; the placeholder example must be trackable. | Git identified `.gitignore` as the ignore rule for `backend/.env`; the file is not tracked. `backend/.env.example` is not ignored and contains only a placeholder. | Pass | None. |
| 15 | Inspect result and zero-result maps. | Leaflet and tile-provider attribution must remain visible. | Both maps exposed a Leaflet attribution link and `© OpenStreetMap contributors`, including the `99999` zero-result state. | Pass | None. |
| 16 | Use Enter from the ZIP input, Enter on a list result, Enter on a map marker, and inspect map zoom controls. | Search and applicable result/map controls must work from the keyboard and expose meaningful accessible names/selected state. | Enter submitted the form; list controls and markers were focusable, named controls with selected state; Enter synchronized selection in both directions after the row 10 correction; Zoom in/out were exposed as buttons. | Pass after correction | Same marker `keypress` correction as row 10. |

## Post-correction automated checks

```text
backend/.venv/bin/python -m pytest backend/tests
68 passed, 2 dependency deprecation warnings

npm --prefix frontend run build
Vite 8.2.2: 13 modules transformed; production build passed

git diff --check
passed with no whitespace errors
```

The browser warning/error log was empty after the corrected rerun. Only the
backend and frontend processes started for this verification were stopped at
the end of the pass.
