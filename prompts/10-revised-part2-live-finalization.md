# Revised Part 2 live finalization — selected evidence

## User direction

The user asked to finish and perfect revised Assignment 2 Part 2, avoid the
earlier mistake where an assessed commit was not available on a public branch,
and leave a single `report.md` submission that links every required public
artifact. When the exact classroom OpenRouter model could not be identified
from the supplied material, the user approved use of the current free model
selected in the OpenRouter account.

## Tool/model disclosure

- OpenAI Codex, GPT-5-based coding agent identified by the development
  environment: repository inspection, implementation, test execution,
  real-browser/database verification, recording, documentation, commit, push,
  and public-link validation.
- OpenRouter `nvidia/nemotron-3.5-lightning:free`: live SQL-proposal and
  grounded-answer calls on October 8, 2026.
- A process-local two-response stub: deterministic tests only; it was not AI
  and was never described as a live provider call.

No credential, authorization header, or `.env` content is included here.

## Verified outcome

The real question asked which saved hotels for leading-zero ZIP `02108` could
provide two rooms from check-in October 10 through checkout October 13, 2026,
and requested the simulated total. The backend displayed the provider's
proposed read-only SQL, independently validated it, executed the bounded query,
retrieved one Beacon Hill record with three nights, minimum availability seven,
and `total_cost_cents=71500`, then sent exactly those records in request two.
The grounded answer reported `$715.00` and explicitly labeled the information
simulated classroom data rather than real inventory.

A real no-match question for 999 rooms executed a valid query, returned zero
records, still made request two, and displayed **No saved hotel matches**. A
November date request displayed **Insufficient saved data** without SQL
execution or a second request. The rejected-write fixture remained separately
labeled and proved that generated `DELETE` SQL did not execute or alter
protected data.

## Genuine failed or revised approaches

1. The first live provider call exceeded the application's 20-second limit
   while the reasoning model generated reasoning tokens. The request was
   revised to use the provider's documented `reasoning_effort: none`, and the
   two-stage live run completed within the bound.
2. A live provider proposal selected `s.searched_zip`, even though the column
   belongs to `saved_hotel_zips`. The validator rejected the query before
   execution. The schema prompt was made explicit about column ownership and
   supplied a valid aggregate query shape; the next real-browser run passed.
3. The insufficient-data response initially omitted an explicit null trace
   field, causing the Vue response validator to reject an otherwise correct
   200 response. FastAPI now preserves the null field; a focused route test and
   real browser rerun passed.
4. A provider response surrounded JSON with prose and included a harmless
   trailing SQL semicolon. Parsing was hardened only enough to extract one JSON
   object and normalize one terminal semicolon. The independent deny-by-default
   SQL authorizer, compile check, work limit, and result limits remain required;
   embedded semicolons, writes, comments, and unauthorized reads still fail.
5. An interrupted screen recording was discarded by macOS. A new fixed-duration
   recording was allowed to finalize, then converted to a GitHub-compatible
   H.264 MP4 with a built-in macOS tool; no dependency was installed.

## Submission safeguard

The assessed implementation commit is written into `report.md` only after that
commit exists, then both the code commit and the follow-up report commit are
pushed to public `main`. Final verification checks the public commit URL, raw
report, linked research/mockup/evidence files, and MP4 without relying on the
local checkout.
