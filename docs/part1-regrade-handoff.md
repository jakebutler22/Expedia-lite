# Assignment 2.1 Part 1 Regrade Handoff

Prepared October 8, 2026 in response to the feedback that the cited commit did
not exist publicly and that the public branches did not contain the Part 1
implementation or demo.

## Public access

- Repository: <https://github.com/jakebutler22/Expedia-lite>
- Public branch containing the work: <https://github.com/jakebutler22/Expedia-lite/tree/main>
- Assessed Part 1 implementation commit: <https://github.com/jakebutler22/Expedia-lite/commit/de43dd9df5c7cc842e9693f29cd43cb85e43507a>
- Report: <https://github.com/jakebutler22/Expedia-lite/blob/main/report.md>
- Recorded Part 1 demo: <https://github.com/jakebutler22/Expedia-lite/raw/refs/heads/main/docs/videos/expedia-lite-part1-demo.mp4>
- Verification record: <https://github.com/jakebutler22/Expedia-lite/blob/main/docs/part1-verification-2026-09-29.md>
- Final professor-style audit: <https://github.com/jakebutler22/Expedia-lite/blob/main/docs/part1-final-audit.md>
- Research: <https://github.com/jakebutler22/Expedia-lite/blob/main/docs/part1-location-research.md>
- Pre-implementation mockup: <https://github.com/jakebutler22/Expedia-lite/blob/main/docs/part1-live-hotel-search-mockup.html>
- AI disclosure/evidence: <https://github.com/jakebutler22/Expedia-lite/blob/main/prompts/07-part-1-live-hotel-search.md>

Anonymous access to the assessed commit page was confirmed on October 8, 2026.
The assessed commit is an ancestor of the public `main` branch. The recording
is a standard MP4 and is also stored in the repository at
`docs/videos/expedia-lite-part1-demo.mp4`.

## What the recording demonstrates

1. A successful live Geoapify search for leading-zero ZIP `02108`.
2. The returned Boston location, current API hotel data, 5 km search label,
   result list, connected Leaflet map, and visible attribution.
3. List selection identifying the same hotel and popup on the map.
4. Marker selection identifying the same hotel in the list.
5. Loading, invalid ZIP (`2108`), unresolved ZIP (`00000`), and no-nearby-hotel
   (`99999`) states.
6. A final successful result state showing that errors do not leave stale
   results presented as current data.

## Canvas submission

Upload the repository-root `report.md`. It contains the required repository,
commit, research, early mockup, demo, verification, MVC/security discussion,
and AI evidence links. The MP4 is linked from the report and does not need to be
uploaded separately unless the instructor specifically asks for a second file.
