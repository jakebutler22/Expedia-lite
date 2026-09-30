# Assignment 2.1 Part 1 final professor-style audit

Audit date: September 29, 2026

The controlling criteria are the Assignment 2.1 Part 1 requirements supplied
for this project. No separate rubric file exists in the repository. The audit
inspected the running application, source, tests, Git configuration, research,
pre-implementation mockup, dated verification evidence, demo script, AI
evidence, `AGENTS.md`, and `report.md`.

## Rubric crosswalk

| Criterion | Assessed evidence | Result |
| --- | --- | --- |
| Intended U.S. postcode | Geocoding sends `postcode`, `type=postcode`, and U.S. filter parameters; normalization accepts only an exact returned postcode and `country_code=us`. Live `00000` returned unresolved without substitution. | Pass |
| Leading-zero ZIP | ZIP stays a string; ASCII five-digit validation accepts `02108`. Live API and Vue both preserved and displayed `02108`. | Pass |
| Live result fidelity | The API count equaled `hotels.length`; Vue rendered the same computed hotel array into named list controls and markers. Provider-derived names, addresses, coordinates, and optional distances matched the response. | Pass |
| Five-kilometre radius | Places uses `filter=circle:{longitude},{latitude},5000` centered on the exact geocoded point, plus a proximity ordering bias. API and UI expose `radius_meters=5000`. | Pass |
| List/map synchronization | One `selectedHotelId` keyed by Geoapify `place_id` drives row state, marker state, popup, and scrolling. Both directions passed browser verification. | Pass after correction |
| Distinct honest states | Ready, loading, results, invalid, unresolved, zero-result, and failed-request states use separate headings and messages. Live and failure checks passed. | Pass |
| No invented hotel facts | The normalizer emits only available provider fields. The live UI contains no price, rating, room, availability, or booking claim. Missing location text falls back only to provider coordinates. | Pass |
| Credential protection | Geoapify calls and configuration remain in FastAPI modules. Ignored `backend/.env` is untracked; the example is placeholder-only. The actual key was absent from 57 candidate files, all Git history, frontend assets, and sampled responses. | Pass |
| MVC clarity | `geocoding.py`, `places.py`, and `hotel_search.py` own provider/domain services; `main.py` owns HTTP mapping; Pydantic owns response shapes; Vue owns rendering and interaction. | Pass |
| Keyboard interaction | Enter submits the form; list results and markers are named, focusable controls with selected state; zoom controls are buttons. The full pass caught and corrected Leaflet marker Enter synchronization. | Pass after correction |
| Research supports design | Geoapify, Leaflet, OpenStreetMap, Google place-search, and Airbnb patterns are linked and translated into explicit project decisions and noted omissions. | Pass |
| Early mockup | `part1-live-hotel-search-mockup.html` is self-contained, labels itself **Pre-implementation mockup**, uses placeholders, and previews every required state before production behavior. | Pass |
| Expected-versus-observed verification | The dated 16-case table records input/action, expectation, observation, result, and correction for every required case. | Pass |
| Live ZIP/date evidence | `16802`, leading-zero `02108`, unresolved `00000`, and zero-result `99999` are explicitly recorded with observation date September 29, 2026; counts are identified as mutable observations. | Pass |
| Demo coverage | `part1-demo-script.md` covers architecture, leading-zero success, loading, radius, list/map synchronization, attribution, invalid/unresolved/zero states, and truthful data boundaries. | Pass |
| AI disclosure/evidence | `prompts/07-part-1-live-hotel-search.md` records the implementation request/outcome and the real failed marker-keyboard approach, correction, and rerun. The report links it. | Pass |
| Report completeness | The report contains submission metadata, research, mockup, decisions, implementation, verification, demo, AI disclosure, scope boundary, and submission checklist. | Pass after final documentation update |
| Scope/no feature creep | No new shortlist, database, authentication, or booking feature was added. Pre-existing Part 2 code remains operational and is explicitly outside the assessed Part 1 scope. | Pass |

## Final automated and application checks

- Backend: 68 tests passed; two dependency deprecation warnings only.
- Frontend: Vite production build passed with 13 transformed modules.
- Part 1 smoke: real `02108` search, loading, result list/map, visible
  attribution, and keyboard marker-to-list synchronization passed.
- Preserved regression smoke: `Harbor` returned T001/T009, `Boston` returned
  T001/T002/T009/T010, and `Miami` showed a no-results state without a table.
- Booking regression: B013 was created for U006 and retained after cancellation;
  disposable B014 was deleted; refresh and a full backend/frontend restart
  preserved those states.
- Restart counts: 8 hotels, 12 trips, 6 users, 9 bookings, one seed marker;
  prior deleted starter B006 and disposable B014 remained absent; the persistent
  next booking number was 15.
- Browser console contained no warning/error entry and no JavaScript dialog.
- `git diff --check` passed. Only test-started processes were stopped.

## Scope note

The repository already contained the SQLite booking workflow before this
Assignment 2.1 Part 1 implementation. It was preserved because `AGENTS.md`
requires working behavior and checkpoints to remain intact. This assignment
added no Part 2 feature; the regression smoke only proves preservation.
