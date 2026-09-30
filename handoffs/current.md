# Current handoff

- **Branch and protected history:** Work remains on `main`. The protected
  historical Part 1 checkpoint remains in Git history under
  `part1-submission`, and the Part 2 checkpoint remains under
  `part2-submission`. The final Assignment 2.1 Part 1 audit is complete; the
  assessed implementation commit is
  `de43dd9df5c7cc842e9693f29cd43cb85e43507a` and is recorded in `report.md`.
- **Live hotel search:** `GET /api/hotels?zip=02108` validates five ASCII
  digits, confirms the exact returned U.S. postcode through Geoapify, and uses
  that returned coordinate as the center of a hard 5 km
  `accommodation.hotel` Places query. It returns a normalized response made
  only from available provider fields. Invalid, unresolved, zero-result,
  configuration, timeout, upstream failure, and success outcomes remain
  distinguishable.
- **Frontend:** Vue shows ready/loading/results/invalid/unresolved/empty/failed
  states, one provider-backed hotel list, and one Leaflet map built from the
  same array. Geoapify `place_id` connects selection in both directions. The
  map frames the confirmed center/results, keeps the 5 km circle and search
  center visible, and retains Leaflet/OpenStreetMap attribution. List buttons,
  markers, map pan/zoom, ZIP input, and submit control support keyboard use.
- **Configuration:** Geoapify configuration now loads from ignored
  `backend/.env`. The credential-free `backend/.env.example` is trackable. The
  key is never placed in Vue or returned by the API. The previously existing
  ignored root `.env` was moved to `backend/.env` without displaying its value.
- **Dependencies:** The approved exact `leaflet@1.9.4` was already present and
  verified. All backend packages were also present. No dependency was added or
  installed during implementation.
- **Checks:** The full backend suite and production frontend build pass. Live
  checks confirmed leading-zero `02108`, unresolved `00000`, zero-result
  `99999`, browser loading/success/error states, synchronized list/marker
  selection, visible attribution, credential isolation, and a clean browser
  warning/error log. The full pass found that Enter on a Leaflet marker opened
  its popup without updating Vue selection; an Enter `keypress` handler was
  added and the affected test, production build, and 68-test backend suite all
  passed on rerun. The exact dated table is in
  `docs/part1-verification-2026-09-29.md`.
- **Artifacts:** Focused research is in `docs/part1-location-research.md`; the
  self-contained early mockup created before production implementation is
  `docs/part1-live-hotel-search-mockup.html`; implementation and demo evidence
  is in `report.md`, `docs/part1-demo-script.md`,
  `docs/part1-final-audit.md`, `docs/verification.md`, and
  `prompts/07-part-1-live-hotel-search.md`.
- **Preserved Part 2 behavior:** SQLite remains the post-seed source of truth.
  Existing sample stay search, booking creation/history, cancellation, and
  deletion code paths were not replaced. Browser verification confirmed
  `Harbor` still returns T001 and T009.
- **Current limitations:** Geoapify data and counts can change over time. The
  classroom application has no authentication, authorization, production
  deployment controls, dedicated frontend linter, or automated Vue
  component/end-to-end suite.
