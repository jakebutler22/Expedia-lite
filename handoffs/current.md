# Current handoff

- **Revised Part 2 status:** The saved-hotel RAG implementation, research,
  pre-implementation mockup, Part-2-first report, evidence log, demo script,
  backend tests, frontend request tests, and real browser/database passes are
  complete. Request one
  proposes one SQL `SELECT` or insufficient-data outcome. A deny-by-default
  SQLite authorizer, table/function allowlists, compile check, and work/result
  limits run before execution. Request two receives the exact validated SQL and
  exact bounded rows. `POST /api/hotel-insights` returns `answer`, `no_matches`,
  `insufficient_data`, or `rejected_query` with a visible safe trace.
- **OpenRouter boundary:** `backend/app/openrouter.py` uses the already-installed
  `httpx` REST client. It accepts only an explicit NVIDIA Nemotron `:free`
  model setting, has no paid/automatic fallback, sends two bounded non-streaming
  requests for a successful query, and returns stage-specific sanitized errors.
  Generated SQL is never trusted: only a validated read from the three saved
  hotel tables can execute. The health route returns status phrases, not values.
- **One genuine blocker:** The exact free Nemotron slug demonstrated in class is
  absent from the repository, nearby course projects, Git history, and supplied
  brief. Add that exact slug and a local OpenRouter key to ignored
  `backend/.env` as `OPENROUTER_MODEL` and `OPENROUTER_API_KEY`, then verify the
  exact catalog entry is still free before the live demo. These values must not
  be pasted into Vue, a `VITE_` variable, evidence, or chat.
- **Branch and protected history:** Work remains on `main`. The protected
  historical Part 1 checkpoint remains in Git history under
  `part1-submission`, and the Part 2 checkpoint remains under
  `part2-submission`. The final Assignment 2.1 Part 1 audit is complete; the
  assessed implementation commit is
  `de43dd9df5c7cc842e9693f29cd43cb85e43507a` and is recorded in `report.md`.
  The revised Part 2 assessed implementation commit is
  `e35c201ab36e83b814a678587646d19816bc3826`; Appendix B records it. The report
  and handoff are intentionally committed afterward because a commit cannot
  truthfully contain a hash that does not exist yet.
- **Local hotel storage backend:** The canonical SQLite database now has
  additive `saved_hotels`, `saved_hotel_zips`, and `demo_hotel_nights` tables.
  `GET /api/saved-hotels`, `POST /api/saved-hotels`, and
  `DELETE /api/saved-hotels/{place_id}` provide ZIP-scoped lookup, atomic
  idempotent saves, and scoped cascade removal. Saves use fixed October 10–14,
  2026 dates and database defaults of 10,000 cents and 20 rooms without
  overwriting later manual edits.
- **Database preservation:** The pre-RAG database was healthy with 8
  Assignment 1 hotels, 12 trips, 6 users, 9 current bookings, one seed marker,
  and booking sequence 15. In addition to the October 6 pre-local-storage
  backup, a verified consistent pre-RAG backup is stored in ignored
  `backend/data/backups/expedia-lite-pre-rag-2026-10-07.db` with SHA-256
  `5fbc9303ad49f9b452aeecf20471de95db2d138645c73a21e115fd715b676166`.
  No RAG schema migration was required.
- **Live hotel search:** `GET /api/hotels?zip=02108` validates five ASCII
  digits, confirms the exact returned U.S. postcode through Geoapify, and uses
  that returned coordinate as the center of a hard 5 km
  `accommodation.hotel` Places query. It returns a normalized response made
  only from available provider fields. Invalid, unresolved, zero-result,
  configuration, timeout, upstream failure, and success outcomes remain
  distinguishable.
- **Frontend:** Every explicit ZIP search now requests
  `GET /api/saved-hotels?zip=<ZIP>` first with caching disabled. A nonempty
  local result is labeled **Saved locally** and never starts the Part 1 hotel
  request; a valid empty result alone falls back to `GET /api/hotels?zip=<ZIP>`
  and is labeled **API results**. Local lookup errors stop without fallback.
  API hotels offer **Add to Local** and saved hotels offer
  **Remove from Local**. Stored October 10–14 nightly rates and room counts are
  shown as simulated classroom data, including valid zeroes. Provider results
  retain the 5 km center/radius overlay; local results use stored coordinates.
  Both sources preserve `place_id` list/marker synchronization and attribution.
- **Configuration:** Geoapify and OpenRouter configuration load from ignored
  `backend/.env`. The trackable `backend/.env.example` has safe Geoapify
  guidance plus blank OpenRouter key/model placeholders. Neither credential is
  placed in Vue or returned by the API.
- **Dependencies:** The approved exact `leaflet@1.9.4` was already present and
  verified. All backend packages were also present. No dependency was added or
  installed during implementation.
- **Checks:** After response-consistency hardening, the full **106-test**
  backend suite, **26-test** focused RAG subset, **23** dependency-free frontend
  request/formatting checks, production Vite build, and rejected-query fixture
  pass. Isolated
  local-hotel tests cover schema enforcement, fixed dates/defaults, leading-zero
  ZIPs, idempotence, manual-edit preservation, atomic rollback, scoped delete,
  fresh committed-value reads, startup preservation, and safe failures. Live
  checks confirmed leading-zero `02108`, unresolved `00000`, zero-result
  `99999`, browser loading/success/error states, synchronized list/marker
  selection, visible attribution, credential isolation, and a clean browser
  warning/error log. The full pass found that Enter on a Leaflet marker opened
  its popup without updating Vue selection; an Enter `keypress` handler was
  added and the affected test, production build, and 68-test backend suite all
  passed on rerun. The exact dated table is in
  `docs/part1-verification-2026-09-29.md`.
- **October 7 local-first re-verification:** The real Vue/FastAPI app was run
  against an isolated temporary database and the live Geoapify-backed Part 1
  route. The request log proved successful-empty ordering
  (`/api/saved-hotels` then `/api/hotels`) and proved that a refreshed local hit
  issued only `/api/saved-hotels`. The browser also confirmed Add/disabled Add,
  all five stored nightly rows, refresh persistence, a committed `$123.45` and
  zero-room edit on reread, explicit no-fallback local failure, scoped removal,
  and keyboard list/marker synchronization. The temporary database was removed
  and the canonical database remained unchanged. Detailed evidence is appended
  to `docs/local-hotel-storage-verification-2026-10-06.md`.
- **Revised Part 2 smoke evidence:** An isolated temporary database plus a
  documented process-local **two-response** provider stub exercised production
  FastAPI/Vue without changing the canonical database. The browser showed the
  fixed Eligible Inn answer, proposed SQL, passed validation, execution status,
  exact retrieved record, request-two status, leading-zero ZIP, checkout
  exclusion, and 67,000-cent/$670.00 total. A `02109` local search showed
  stored nights/map/attribution. This is not claimed as live OpenRouter. The
  first real Uvicorn run exposed cross-thread SQLite cleanup; the connection
  setting and a regression test were corrected, and final real request paths
  returned 200. See `docs/revised-part2-evidence-log-2026-10-07.md` E14.
- **Artifacts:** Focused research is in `docs/part1-location-research.md`; the
  self-contained early mockup created before production implementation is
  `docs/part1-live-hotel-search-mockup.html`; implementation and demo evidence
  is in `report.md`, `docs/part1-demo-script.md`,
  `docs/part1-final-audit.md`, `docs/verification.md`, and
  `prompts/07-part-1-live-hotel-search.md`.
- **Revised artifacts:** RAG research is
  `docs/revised-part2-rag-research.md`; the explicitly pre-implementation
  chatbot mockup is `docs/revised-part2-chatbot-early-mockup.html`; dated
  implementation evidence is `docs/revised-part2-evidence-log-2026-10-07.md`;
  the demo procedure is `docs/revised-part2-demo-script.md`; the fixed sample is
  `backend/tests/fixtures/revised_part2_fixed_sample.json`; and selected AI
  evidence is `prompts/08-revised-part2-rag.md` plus
  `prompts/09-revised-part2-final-verification.md`.
- **Preserved Part 2 behavior:** SQLite remains the post-seed source of truth.
  Existing sample stay search, booking creation/history, cancellation, and
  deletion code paths were not replaced. Browser verification confirmed
  `Harbor` still returns T001 and T009. Browser checks also confirmed the
  local-empty/API-fallback label, Add state, five nightly rows, refresh
  persistence, a committed `$0.00`/zero-room edit on the next explicit search,
  and a local-hit map using the saved coordinate without another Part 1
  request.
- **Current limitations:** Geoapify data and counts can change over time. The
  classroom application has no authentication, authorization, production
  deployment controls, dedicated frontend linter, or automated Vue
  component/end-to-end suite. The frontend request orchestration does have a
  dependency-free Node test suite.
- **October 8 canonical checkpoint:** The real application saved Beacon Hill
  Hotel and Bistro and Churchill at Boston View for `02108`. DB Browser for
  SQLite 3.13.1 opened the canonical database, committed Beacon Hill's
  `2026-10-10` values from 10,000 cents/20 rooms to 15,750 cents/7 rooms with
  **Write Changes**, and Vue reread `$157.50`/`7` without restart and after a
  full backend/frontend restart. Replaying the original save kept five nights
  and preserved the edit. Removing Churchill left Beacon Hill intact. The
  local-hit request log contained only `/api/saved-hotels`; all protected
  Assignment 1 tables were byte-for-row identical to the pre-checkpoint backup.
- **Remaining handoff:** The canonical database retains Beacon Hill as the live
  RAG comparison row. The real OpenRouter key/model are not configured, so the
  genuine two-request provider run, final recording, public video URL, assessed
  commit, push, and anonymous-link checks are pending. The exact walkthrough is
  `docs/revised-part2-demo-script.md`. No app or dependency was installed.
