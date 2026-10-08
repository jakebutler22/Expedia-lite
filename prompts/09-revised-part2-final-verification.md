# Selected prompt — Revised Part 2 final verification

## Purpose

Verify the final revised Part 2 implementation against the two-model-request
benchmark, preserve the existing Expedia Lite application and database, and
prepare the reproducible report and recorded-demonstration handoff.

## Supplied constraints

- A successful question must make model request one for a SQL proposal, then
  validate and execute that SQL, then make model request two with the exact
  retrieved records.
- Use isolated temporary databases and clearly labeled fixtures for mutation
  and failure checks. Never run destructive verification against the real
  assignment database.
- Verify date and room rules, integer-cent totals, leading-zero ZIPs, duplicate
  ZIP associations, rejected SQL, query/result limits, malformed responses,
  and simulated rate limits.
- Preserve local save/remove behavior, committed-value rereads, Part 1 ZIP and
  5 km behavior, list/map synchronization, honest states, and original
  Assignment 1 records.
- Record live OpenRouter evidence only if the real key and exact class model ID
  are configured. Otherwise mark the demonstration pending; never guess the
  model or treat a stub as live evidence.
- Keep the required DB Browser Write Changes checkpoint manual unless it is
  genuinely observed.
- Do not install a dependency without approval, publish the repository, change
  its visibility, upload a recording, or submit to Canvas.

## Resulting implementation and verification changes

The first chatbot implementation used application-owned static SQL followed by
one model request. That design did not meet the later two-request benchmark. It
was replaced by a pipeline in which request one proposes one `SELECT`, a
deny-by-default SQLite authorizer and independent size/work limits validate and
execute it, and request two receives the original question, validated SQL, and
exact retrieved rows. Rejected SQL is not executed and does not reach request
two; a successfully executed empty query does reach request two.

A labeled fixed JSON fixture now covers checkout exclusion, missing and sold-out
nights, insufficient rooms, integer-cent totals, a leading-zero ZIP, duplicate
ZIP associations, out-of-coverage questions, unsafe SQL, result/work limits,
malformed provider output, and simulated rate limits. Final checks passed with
104 backend tests, 21 frontend tests, and a production frontend build.

## Genuine failed or revised approaches

1. **Architecture revision:** the one-request/static-query design was rejected
   as noncompliant with the later benchmark and replaced with the two-request
   validated-SQL pipeline. The decision and final controls are recorded in
   `docs/revised-part2-rag-research.md` and entries E12–E15 of
   `docs/revised-part2-evidence-log-2026-10-07.md`.
2. **Real-server database-thread failure:** the first actual Uvicorn smoke run
   raised `sqlite3.ProgrammingError` because FastAPI could close a synchronous
   generator dependency on a different worker thread. `connect_database` was
   changed to open each request-owned connection with
   `check_same_thread=False`, and a cross-thread-close regression test was
   added. The complete suites and real request paths then passed. This is
   recorded in evidence entry E14.
3. **Verification harness corrections:** the first fixed-fixture test omitted
   database initialization, and the first standalone fixture-script run could
   not resolve the application package. The test was initialized through the
   production schema path, the script added its project root to its import
   path, and both reruns passed. These were harness corrections, not changes to
   the protected assignment database.

## Evidence boundary

The actual browser run used the production Vue/FastAPI application, an isolated
temporary SQLite database populated from the fixed JSON sample, and a clearly
labeled process-local two-response provider stub. It verified the visible
two-stage trace but is not a live OpenRouter success. Safe configuration
inspection found no local `OPENROUTER_API_KEY` or `OPENROUTER_MODEL`, so the
genuine live-provider capture, actual model ID, DB Browser checkpoint, and video
URL remain pending user actions.
