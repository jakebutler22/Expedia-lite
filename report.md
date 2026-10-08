# Expedia Lite — Revised Assignment 2 Part 2

## Submission record

- Public repository: [github.com/jakebutler22/Expedia-lite](https://github.com/jakebutler22/Expedia-lite)
- Public branch: [`main`](https://github.com/jakebutler22/Expedia-lite/tree/main)
- Assessed Part 2 commit: **__ASSESSED_COMMIT__**
- Screen-recorded demonstration: [public MP4](https://github.com/jakebutler22/Expedia-lite/raw/refs/heads/main/docs/videos/expedia-lite-revised-part2-demo.mp4)
- Rejected-query video evidence: [public MP4 supplement](https://github.com/jakebutler22/Expedia-lite/raw/refs/heads/main/docs/videos/expedia-lite-rejected-query-supplement.mp4)
- Submission file: `report.md` (this file)
- Observation date for the final local/database checks: **October 8, 2026**

This report is intentionally Part 2 first because it is the file submitted for
the revised Part 2 assignment. The corrected Part 1 submission remains
preserved at public commit
[`de43dd9df5c7cc842e9693f29cd43cb85e43507a`](https://github.com/jakebutler22/Expedia-lite/commit/de43dd9df5c7cc842e9693f29cd43cb85e43507a),
including its [Part 1 report](https://github.com/jakebutler22/Expedia-lite/blob/de43dd9df5c7cc842e9693f29cd43cb85e43507a/report.md)
and [public MP4](https://github.com/jakebutler22/Expedia-lite/raw/refs/heads/main/docs/videos/expedia-lite-part1-demo.mp4).

## 1. Project access, startup, and configuration

Clone the public repository and start the backend from the repository root:

```bash
cd "/Users/jakebutler/Documents/ChatGPT/Expedia-lite"
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Start Vue in a second Terminal window:

```bash
cd "/Users/jakebutler/Documents/ChatGPT/Expedia-lite"
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173`; FastAPI documentation is at
`http://127.0.0.1:8000/docs`. The actual SQLite database is
`backend/data/expedia-lite.db`.

Copy `backend/.env.example` to ignored `backend/.env` and provide only the
backend settings:

```dotenv
GEOAPIFY_API_KEY=<your Geoapify key>
OPENROUTER_API_KEY=<your OpenRouter key>
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
```

Neither provider key belongs in Vue, a `VITE_` value, Git, the report, or the
recording. `.gitignore` excludes `.env` and runtime SQLite files while
`backend/.env.example` remains trackable. Expedia Lite accepts only an explicit
NVIDIA Nemotron `:free` model setting and has no silent paid or automatic
fallback. The key used for verification was short-lived and remains only in
the ignored backend file; it is absent from Git, the frontend, responses,
evidence, and the recording.

No dependency was added during revised Part 2. The existing `httpx` client,
Python `sqlite3`, Vue, and approved `leaflet@1.9.4` were sufficient.

## 2. Research notes and resulting decisions

The complete source-linked research is
[docs/revised-part2-rag-research.md](https://github.com/jakebutler22/Expedia-lite/blob/main/docs/revised-part2-rag-research.md).
It was started October 7, 2026 before chatbot implementation and rechecked
October 8 before final verification.

Important sources and decisions:

- [OpenRouter quickstart](https://openrouter.ai/docs/quickstart),
  [chat-completion API](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request),
  [free model variants](https://openrouter.ai/docs/guides/routing/model-variants/free),
  [models API](https://openrouter.ai/api/v1/models), and
  [pricing](https://openrouter.ai/pricing/) support one backend-only REST
  integration. A `:free` suffix is used only for a catalog entry that actually
  lists it; no paid fallback is allowed. The October 8 catalog showed several
  different free Nemotron entries. The class materials available to this
  project did not name one exact slug, so the final run explicitly selected
  and recorded the current zero-price catalog entry
  `nvidia/nemotron-3.5-lightning:free` rather than pretending it was the
  unnamed classroom slug.
- [Python `sqlite3`](https://docs.python.org/3/library/sqlite3.html) and
  [SQLite security guidance](https://www.sqlite.org/security.html) informed the
  deny-by-default authorizer, compile check, and query/result limits. The model
  never receives the database or a connection and cannot directly execute SQL.
- [Geoapify Geocoding](https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/)
  and [Places](https://apidocs.geoapify.com/docs/places/) support the preserved
  exact U.S. postcode confirmation and hard 5 km hotel search. Their location
  facts do not prove real rooms, rates, availability, or booking status.
- [Leaflet](https://leafletjs.com/reference.html) supports the retained
  keyboard-usable map, marker events, bounds, popups, and attribution.
- Booking.com property-question and trip-planner patterns and Expedia's
  conversational trip-planning pattern support placing a concise question
  near structured hotel results. Their weakness for this assignment is that a
  fluent response can look authoritative without visible grounding.

Expedia Lite therefore shows the proposed SQL, backend validation decision,
execution status, exact retrieved rows, whether request two was sent, and the
grounded answer. It uses no embeddings, vector database, agent framework,
conversation memory, payment, booking, or real inventory claims.

## 3. Early mockup

[Open the self-contained early chatbot mockup.](https://github.com/jakebutler22/Expedia-lite/blob/main/docs/revised-part2-chatbot-early-mockup.html)

The mockup was created **before revised Part 2 production implementation**. It
shows the natural-language question, loading, answer, no-match,
insufficient-data, and error states beside the existing saved hotel/list/map
workflow.

The early design assumed application-owned static SQL and one model request. A
later explicit benchmark required a model-proposed query and two model requests
with checked retrieval between them. Production was revised to expose proposed
SQL, validation, bounded execution, exact records, and second-request status.
This is a real documented design revision, not a retrospective fabricated
failure.

## 4. Implementation and MVC responsibilities

### Local-first hotel storage

Every explicit ZIP search first calls
`GET /api/saved-hotels?zip=<five-digit ZIP>` with browser caching disabled.
A nonempty local success displays **Saved locally**, stored coordinates, and
the five current committed nightly records; it makes no Part 1 hotel-search
request. Only a successful empty local response falls back to
`GET /api/hotels?zip=<ZIP>` and displays **API results**. A local network, HTTP,
or invalid-response failure remains an error and never becomes an empty success.

**Add to Local** stores the real provider identity, available hotel details,
coordinates, and searched ZIP. Add is disabled while pending and whenever the
persisted data says the hotel is already saved. **Remove from Local** appears
only for saved hotels. Saves are idempotent and do not overwrite later manual
night edits. Requests open a fresh SQLite connection, so each repeated search
reads current committed values rather than localStorage, an in-memory result,
or stale server/browser cache.

The normalized tables are separate from the supplied Assignment 1 `hotels`
table:

- `saved_hotels`: unique provider ID, name, address, latitude, longitude;
- `saved_hotel_zips`: unique hotel/leading-zero ZIP association;
- `demo_hotel_nights`: unique hotel/date rows with database defaults of 10,000
  cents and 20 rooms for October 10–14, 2026.

The nightly values are always labeled **simulated classroom data**. Integer
cents are formatted accurately (`10000` → `$100.00`), and valid zeroes are not
replaced with defaults.

### Two-request RAG workflow

`POST /api/hotel-insights` accepts one saved-hotel question up to 500
characters.

1. FastAPI sends the question and the three-table schema/rules to the one
   configured model. The model may propose exactly one `SELECT` or return
   `insufficient_data`.
2. FastAPI, not the model, validates the proposal. It rejects comments,
   semicolons, multiple statements, writes, administrative/extension work,
   unauthorized tables/functions, excess VM work, and oversized results. A
   SQLite authorizer allows reads only from `saved_hotels`,
   `saved_hotel_zips`, and `demo_hotel_nights`.
3. FastAPI executes only a passed query with limits of 50 rows, 20 columns,
   50,000 serialized bytes, and bounded virtual-machine work.
4. FastAPI sends the original question, validated SQL, and exact retrieved JSON
   records to the same model. An empty successful retrieval still reaches this
   second request so it can return `no_matches`.
5. The backend and frontend reject contradictions such as an `answer` with
   zero records, `no_matches` with nonempty records, a changed model ID, or
   trace flags that do not describe a valid pipeline state.

For the selected reasoning-capable model the backend explicitly sends
`reasoning_effort: none`, which removed an observed 20-second timeout while
leaving SQL and answer generation intact. It also safely accepts JSON wrapped
in provider prose and removes only a single trailing SQL semicolon before the
deny-by-default validator runs; embedded semicolons and multiple statements
remain rejected. The date-range prompt includes the actual table ownership and
a valid aggregate query shape so `searched_zip`, checkout exclusion, minimum
rooms, and integer-cent totals are generated consistently.

The user sees distinct `answer`, `no_matches`, `insufficient_data`,
`rejected_query`, loading, and failed-request states. All provider errors are
stage-specific but sanitized.

### MVC boundary

- **Model/data services:** SQLite schema, one-time CSV seed, saved-hotel access,
  safe SQL rules, Geoapify services, and OpenRouter client live in
  `backend/app/` without Vue responsibility.
- **Controller/API:** FastAPI validates HTTP input, coordinates services,
  normalizes responses, and maps errors without exposing secrets.
- **View:** Vue owns forms, status presentation, loading/error states, formatted
  simulated values, selection, and synchronized Leaflet list/map interaction.

The four supplied CSVs remain immutable one-time seed inputs. After seeding,
SQLite is the source of truth; no request path rereads a CSV. Existing search,
booking creation/history, cancellation, and permanent deletion remain intact,
and cancellation is still different from deletion.

## 5. Verification evidence

The detailed chronology and complete expected-versus-observed evidence are in
[docs/revised-part2-evidence-log-2026-10-07.md](https://github.com/jakebutler22/Expedia-lite/blob/main/docs/revised-part2-evidence-log-2026-10-07.md).
The repeatable sample is
[backend/tests/fixtures/revised_part2_fixed_sample.json](https://github.com/jakebutler22/Expedia-lite/blob/main/backend/tests/fixtures/revised_part2_fixed_sample.json)
and is explicitly labeled fixture-only.

Run all checks from the repository root:

```bash
backend/.venv/bin/python -m pytest -q backend/tests
npm --prefix frontend test
npm --prefix frontend run build
backend/.venv/bin/python backend/scripts/revised_part2_fixture_demo.py
```

### Final automated and fixed-sample results

| Input/action | Expected result | Observed result | Pass/fail | Correction or limitation |
| --- | --- | --- | --- | --- |
| Full backend suite | Existing booking, Part 1, local storage, safe SQL, and RAG behavior pass in isolated databases. | **107/107 passed** in 0.57 seconds; the focused RAG subset was **27/27**. | Pass | Two dependency deprecation warnings do not affect behavior; no package change was made. |
| Frontend tests and production build | Request contracts, formatting, failures, and build pass. | **23/23 tests passed**; Vite transformed 15 modules and built production output in 116 ms. | Pass | No new test dependency was needed. |
| Fixed `02108`, Oct. 10 check-in/Oct. 13 checkout, two rooms | Request one → checked SQL → exact rows → request two; checkout excluded; integer-cent total. | Eligible Inn had three included nights, minimum two rooms, and **67,000 cents ($670.00)**; Oct. 13 checkout data was excluded. | Pass | Deterministic fixture, not a live provider result. |
| Duplicate ZIP associations; missing middle night; sold-out night; insufficient rooms | No duplicate totals; incomplete/ineligible hotels excluded. | Each rule produced the expected exact record set and total. | Pass | Fixture data. |
| Successful empty retrieval | Request two runs and returns `no_matches`. | Exact empty list reached request two and returned `no_matches`. | Pass | Simulated provider response. |
| November 2026 request | No SQL or second request because stored coverage is only Oct. 10–14. | `insufficient_data`; validation not run; execution and request two were false. | Pass | Simulated provider response. |
| `DELETE`, multiple statements, unauthorized table, `PRAGMA`, `ATTACH`, extension | Reject before execution/request two; all protected data unchanged. | All were rejected. The fixture demo reported execution false, second-request calls zero, protected data unchanged, and temporary DB removed. | Pass | Labeled fixture; no live quota used. |
| Malformed model payloads, contradictory status/rows, invalid trace, simulated 429 | Honest stage-specific failure and no unsafe success state. | All invalid responses followed the expected failure path. New tests reject answer/no-match and trace contradictions on both backend and frontend. | Pass | 429 is simulated to avoid consuming quota. |
| Credential boundary | `.env` ignored; key absent from Vue, build, health, and errors. | Ignore checks and response/source tests passed; safe example contains blanks only. | Pass | Real secrets are intentionally absent from evidence. |

### October 8 real application and database observations

| Input/action | Expected result | Observed result | Pass/fail | Correction made |
| --- | --- | --- | --- | --- |
| Search leading-zero `02108` with empty local tables | Local lookup first; empty success falls back to the preserved exact-postcode/5 km API route. | Request log showed `/api/saved-hotels?zip=02108` then `/api/hotels?zip=02108`. Vue showed **API results**, 5 km, map attribution, and 19 live hotels on **October 8, 2026**. | Pass | Result count is an observation, never a fixed assertion. |
| Add Beacon Hill Hotel and Bistro and Churchill at Boston View | Provider identities/details/coordinates, searched ZIP, and five nights persist; Add disables. | Both saved with five Oct. 10–14 rows; Add disabled and Remove appeared. | Pass | None. |
| Repeat `02108` | **Saved locally**; no Part 1 hotel request; exact stored coordinates and list/map dataset. | Vue showed two saved hotels. The new request-log segment contained only `/api/saved-hotels?zip=02108`. | Pass | None. |
| DB Browser edit Beacon Hill Oct. 10 from 10,000 cents/20 rooms to 15,750/7 and click **Write Changes** | Commit to the active database and reread without restart. | DB Browser reported one row affected; **Write Changes** was clicked and disabled after commit. Repeated Vue search showed **$157.50** and **7**. | Pass | Initial direct editor setting did not populate the native control; normal paste was used and the successful run was visibly verified. |
| Replay Beacon Hill's actual save payload | Exactly five rows remain and the edit is not overwritten. | HTTP 201 returned five nights; SQL showed `night_count=5`, `edited_row_preserved=1`. | Pass | None. |
| Remove only Churchill; repeat search | Churchill disappears with dependent rows; Beacon Hill remains with edited data. | DELETE returned HTTP 200; Vue then showed one saved hotel, Beacon Hill, `$157.50`, and `7`. | Pass | Browser reread was genuine; frontend request tests separately cover the Remove control. |
| Stop/restart only this run's backend and frontend; press Enter on ZIP input | SQLite persistence and keyboard submission survive a full restart. | After restart, Enter returned **Saved locally**, Beacon Hill, `$157.50`, and `7`. | Pass | None. |
| Compare all protected Assignment 1 tables with the pre-checkpoint backup | No original record changes; healthy database. | Bidirectional comparisons showed zero differing rows for `hotels`, `users`, `trips`, `bookings`, `booking_id_sequence`, and `seed_metadata`; integrity `ok`; no foreign-key violations. | Pass | None. |
| Ask while provider configuration is absent; inspect console | Honest failure leaves other features usable; no application console errors. | Vue showed **Saved hotel insights unavailable** with the configuration message and preserved hotel features; warning/error log was empty. | Pass | This is failure-state evidence, not the required live success. |

### Live provider result

The following observations used the real backend, canonical SQLite database,
and OpenRouter on **October 8, 2026**. The actual model returned in every trace
was `nvidia/nemotron-3.5-lightning:free`; the October 8 Models API listed that
exact entry with zero prompt and completion price. No key or authorization
header entered browser-visible code or evidence.

| Input/action | Expected result | Observed result | Pass/fail | Correction made |
| --- | --- | --- | --- | --- |
| Ask: “Which saved hotels for ZIP 02108 can provide 2 rooms from check-in 2026-10-10 through checkout 2026-10-13, and what is the simulated total cost?” | Request one proposes read-only SQL; validation passes; exact SQLite rows execute; request two returns a grounded answer. | The trace showed the exact model, passed SQL, execution true, second request true, and one Beacon Hill record: `searched_zip=02108`, `stay_nights=3`, `minimum_rooms_available=7`, `total_cost_cents=71500`. The answer reported **$715.00** and explicitly called the data simulated classroom data, not live inventory. | Pass | The first live attempt timed out because this reasoning model spent the 20-second limit reasoning. Adding the officially supported `reasoning_effort: none` produced a complete response while preserving both model stages. |
| Repeat the same question in the real Vue interface | The same safe pipeline is visible to the user and the retrieved record selects the same list/map hotel. | Vue displayed **Grounded answer**, the model ID, proposed SQL, validation `passed`, bounded execution, exact record, second request sent, and the `$715.00` answer. | Pass | A later provider proposal incorrectly selected `s.searched_zip`; SQLite validation rejected it without execution. The schema prompt was tightened with explicit column ownership and a valid aggregate query shape, then the browser rerun passed. |
| Ask for at least 999 rooms on each included night | A valid query executes to an empty list, request two still runs, and the UI shows no-match rather than failure/insufficient data. | Vue displayed **No saved hotel matches**, zero retrieved records, validation `passed`, execution true, and the second request sent. | Pass | The prompt now states that a large numeric room count must be queried rather than guessed as insufficient. |
| Ask for Nov. 10–13, 2026 | Coverage is outside Oct. 10–14, so no SQL or second request runs. | Vue displayed **Insufficient saved data**, validation `not_run`, execution false, second request false, and zero records. | Pass | FastAPI stopped excluding the explicit `proposed_sql: null` trace field; this corrected a real frontend contract failure for early insufficient outcomes. |
| Provider adds prose around JSON or one trailing SQL semicolon | Preserve safe provider content without weakening SQL security. | Regression tests pass with prose-wrapped JSON and one trailing semicolon. The subsequent query still crosses the full authorizer/compile/work/result validation boundary. | Pass | Parser now extracts one JSON object; only a sole trailing semicolon is normalized. Embedded semicolons, multiple statements, writes, comments, and unauthorized access still fail. |

## 6. Screen-recorded demonstration

- Public MP4: [Expedia Lite Revised Part 2 demo](https://github.com/jakebutler22/Expedia-lite/raw/refs/heads/main/docs/videos/expedia-lite-revised-part2-demo.mp4)
- Public safety supplement: [rejected-query fixture video](https://github.com/jakebutler22/Expedia-lite/raw/refs/heads/main/docs/videos/expedia-lite-rejected-query-supplement.mp4)
- Local repository path: `docs/videos/expedia-lite-revised-part2-demo.mp4`
- Download copy: `~/Downloads/Expedia-Lite-Revised-Part-2-Demo.mp4`
- Actual model/date: `nvidia/nemotron-3.5-lightning:free`, October 8, 2026
- File verification: H.264 in an ISO MP4 v2 container, 1280 × 828, 104.88 seconds, approximately 51 MB; SHA-256 `397e01c83f64eb4181d7a8453afef20ae5b4266982631c4163d6ff197ad641de`

The exact seven-part walkthrough is
[docs/revised-part2-demo-script.md](https://github.com/jakebutler22/Expedia-lite/blob/main/docs/revised-part2-demo-script.md).
The final recording shows:

1. a leading-zero ZIP local hit labeled **Saved locally**, all five stored
   nights, map/list synchronization, and attribution;
2. one successful real question through model request one, proposed SQL,
   validation/execution, exact records, model request two, and answer;
3. the answer compared with actual SQLite rows;
4. a distinct successful-empty **No saved hotel matches** case with a passed,
   executed query and zero retrieved records.

The report/evidence log supplies the expected-versus-observed insufficient,
DB Browser **Write Changes**, restart, scoped-removal, and Assignment 1
preservation checks. A 14.88-second H.264 safety supplement visibly shows the
labeled fixture's proposed `DELETE`, rejected validation, execution false,
zero second-model calls, protected data unchanged, and temporary database
removal. Its SHA-256 is
`6cbab6c396d0bd33c33059ab3d5bb33a29736fe92e8d6945d724fbbab5047a15`;
the matching accessible text artifact is
[docs/revised-part2-rejected-query-evidence.html](https://github.com/jakebutler22/Expedia-lite/blob/main/docs/revised-part2-rejected-query-evidence.html).
Neither recording contains a credential, and both were compressed below
GitHub's single-file limit without installing software.

## 7. AI disclosure and evidence log

| Tool/model actually used | Purpose and boundary |
| --- | --- |
| OpenAI Codex, GPT-5-based coding agent identified by the development environment | Repository audit, research synthesis, implementation, tests, browser/DB Browser verification, corrections, documentation, Git, and recording preparation. Every claim was checked against code, tests, database state, or the running UI. |
| Codex web retrieval with the same agent | Official OpenRouter/Geoapify/library research and public-link checks; it was not hotel application data. |
| Process-local two-response stub | Deterministic testing only; it is **not AI** and is never claimed as live OpenRouter. |
| OpenRouter `nvidia/nemotron-3.5-lightning:free` | Live October 8, 2026 SQL proposal and grounded-answer generation. The public trace records the exact model, proposed SQL, retrieved records, and answer; the private key is omitted. |

Selected prompt/evidence excerpts are public in
[prompts/08-revised-part2-rag.md](https://github.com/jakebutler22/Expedia-lite/blob/main/prompts/08-revised-part2-rag.md)
and
[prompts/09-revised-part2-final-verification.md](https://github.com/jakebutler22/Expedia-lite/blob/main/prompts/09-revised-part2-final-verification.md).
[The final live-run record](https://github.com/jakebutler22/Expedia-lite/blob/main/prompts/10-revised-part2-live-finalization.md)
documents the user-approved model choice, live questions/results, genuine
failed and revised approaches, and public-submission safeguard. Together these
records connect requirements to the two-request service, safe-SQL boundary,
fixed sample, visible trace, and expected-versus-observed checks.

Six genuine revisions are retained:

1. The early one-request/static-query design failed the later explicit
   two-request/generated-SQL benchmark and was replaced.
2. A real Uvicorn run exposed cross-thread SQLite dependency cleanup; connection
   setup and a regression test were corrected before endpoint reruns passed.
3. The first DB Browser editor attempt did not actually enter the SQL. The
   unchanged database exposed the failure; normal paste, execution, **Write
   Changes**, a direct database read, Vue reread, and restart rerun then passed.
4. The first live model call timed out with default reasoning. The official
   `reasoning_effort: none` option reduced it to a successful bounded request.
5. A live proposal used `s.searched_zip`, a nonexistent column. The validator
   rejected it before execution; explicit schema ownership and a safe aggregate
   query shape corrected the next real-browser run.
6. The first screen-capture attempt included an honest provider-format failure,
   and an interrupted retry was discarded by macOS. Provider JSON parsing was
   safely hardened, the entire browser sequence was rerun, and the final fixed-
   duration capture was allowed to finalize before H.264 conversion.

## 8. Security, scope, and submission checklist

- Public repository and branch: complete; the immutable assessed commit is
  listed at the top of this report and was checked anonymously after push.
- Research with links, useful/problematic observations, limits, and decisions:
  complete.
- Early pre-implementation mockup with subsequent revision explained:
  complete.
- Working local-storage foundation and full two-request RAG implementation:
  complete.
- Expected-versus-observed evidence, fixed JSON, live ZIP/date, live provider,
  DB Browser **Write Changes**, restart, and preservation checks: complete.
- Public screen recordings covering live success/no-match and rejected-query
  safety, with no credential exposure: complete.
- AI disclosure with actual models, prompts, verification, and genuine
  revised/failed approaches: complete.
- `.env` ignored, keys backend-only, safe example committed: complete.
- No vector database, unrelated framework, paid fallback, real inventory,
  booking claim, deployment, or feature creep was introduced.

All required submission artifacts are linked from this report. The only Canvas
upload is this `report.md`; its public links provide the code, assessed commit,
research, pre-implementation mockup, expected-versus-observed evidence, AI
evidence, and MP4 without requiring an additional access request.
