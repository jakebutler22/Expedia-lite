# Expedia Lite — Part 1

## Repository and commit

Repository URL: [github.com/jakebutler22/Expedia-lite](https://github.com/jakebutler22/Expedia-lite)

Exact Part 1 implementation commit: [`cf2f1945bb9fcec38842530caf25657bd2385f1f`](https://github.com/jakebutler22/Expedia-lite/commit/cf2f1945bb9fcec38842530caf25657bd2385f1f)

## Implementation

The Vue frontend collects a city, requests matching stays from FastAPI, and displays either a clearly labeled table or a direct no-results message. FastAPI validates the query and defines the JSON boundary. The Python search service reads `hotels.csv` and `trips.csv`, joins them through `hotel_id`, compares city names case-insensitively, and derives night counts and estimated stay prices.

## Verification

Verification was performed on September 9, 2026.

| Action | Expected result | Observed result |
| --- | --- | --- |
| Run backend tests | CSV join, normalization, empty result, API response, and blank-query behavior pass. | All 5 tests passed. |
| Build the Vue frontend | Vite completes a production build without errors. | Build passed; 11 modules were transformed. |
| Open the frontend | The search interface and initial guidance are visible. | Expedia Lite heading, labeled City input, Search button, and guidance were visible. |
| Search `Boston` | T001, T002, T009, and T010 appear. | Four joined rows appeared with those IDs, hotel details, dates, nights, and prices. |
| Search `boston` | Matching ignores capitalization. | The same four trip IDs appeared. |
| Search `Miami` | A clear no-results message appears and the results table is absent. | “No hotel stays found for Miami. Try another city.” appeared; the page contained zero tables. |
| Submit whitespace-only input | The interface asks for a city without showing stale results. | “Enter a city to search for available stays.” appeared; the page contained zero tables. |
| Inspect the browser console | No application warnings or errors. | No warning or error entries were recorded. |

Screenshots: [Boston search results](https://github.com/jakebutler22/Expedia-lite/blob/cf2f1945bb9fcec38842530caf25657bd2385f1f/docs/screenshots/part1-boston-results.jpg) and [Miami no-results state](https://github.com/jakebutler22/Expedia-lite/blob/cf2f1945bb9fcec38842530caf25657bd2385f1f/docs/screenshots/part1-miami-no-results.jpg).

## Project context and next steps

- [Setup and run instructions](https://github.com/jakebutler22/Expedia-lite/blob/cf2f1945bb9fcec38842530caf25657bd2385f1f/README.md)
- [Project-specific agent instructions](https://github.com/jakebutler22/Expedia-lite/blob/cf2f1945bb9fcec38842530caf25657bd2385f1f/AGENTS.md)
- [Design pipeline](https://github.com/jakebutler22/Expedia-lite/blob/cf2f1945bb9fcec38842530caf25657bd2385f1f/docs/design-pipeline.md)
- [Verification procedure](https://github.com/jakebutler22/Expedia-lite/blob/cf2f1945bb9fcec38842530caf25657bd2385f1f/docs/verification.md)
- [Selected setup prompt](https://github.com/jakebutler22/Expedia-lite/blob/cf2f1945bb9fcec38842530caf25657bd2385f1f/prompts/01-project-setup.md)
- [Selected Part 1 prompt](https://github.com/jakebutler22/Expedia-lite/blob/cf2f1945bb9fcec38842530caf25657bd2385f1f/prompts/02-part-1-search.md)
- [Current handoff](https://github.com/jakebutler22/Expedia-lite/blob/main/handoffs/current.md)

Remaining limitation: Part 1 reads CSV files and does not persist data. The next task is Part 2: seed SQLite once and add booking create, read, cancel, and delete workflows through FastAPI and Vue while preserving this Part 1 checkpoint.
