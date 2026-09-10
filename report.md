# Expedia Lite — Part 1

## Repository and commit

Repository URL: [github.com/jakebutler22/Expedia-lite](https://github.com/jakebutler22/Expedia-lite)

Part 1 implementation commit: [`cf2f1945bb9fcec38842530caf25657bd2385f1f`](https://github.com/jakebutler22/Expedia-lite/commit/cf2f1945bb9fcec38842530caf25657bd2385f1f).

Submitted checkpoint: this commit, titled `Align verification doc and correct verification dates`. It contains the aligned verification record, corrected dates, completed report, handoff, regenerated browser evidence, and verified application implementation. Its exact hash is recorded in the immediately following documentation commit and by the annotated Git tag `part1-submission`.

## Implementation

The Vue frontend collects a city, requests matching stays from FastAPI, and displays either a clearly labeled table or a direct no-results message. FastAPI validates the query and defines the JSON boundary. The Python search service reads `hotels.csv` and `trips.csv`, joins them through `hotel_id`, compares city names case-insensitively, and derives night counts and estimated stay prices.

## Verification

Verification was performed on September 9-10, 2026.

| Action | Expected result | Observed result |
| --- | --- | --- |
| Manually review every changed file in VS Code Source Control | Confirm that only the backend reads CSVs, hotels and trips join on `hotel_id`, the frontend calls FastAPI, every results-table column has a clear heading, and no SQLite or booking CRUD entered Part 1. | Completed a file-by-file Source Control review. Confirmed `backend/app/search.py` is the only layer reading CSVs and joins hotels to trips on `hotel_id`; `frontend/src/App.vue` calls the FastAPI endpoint and supplies headings for all eight table columns; no SQLite or booking CRUD code is present. |
| Run the CHECK → TAKE ACTION → VERIFY dependency cycle | Identify the project Python interpreter and Node/npm versions, install only missing project dependencies, then verify the selected environments and imports. | CHECK used Python 3.14.7 at `backend/.venv/bin/python`, Node v24.12.0, and npm 11.6.2; FastAPI/Uvicorn and the project-local Vue packages required installation. TAKE ACTION installed `backend/requirements.txt` into `backend/.venv` and the frontend packages into `frontend/node_modules`. VERIFY reran the version commands and successfully imported FastAPI 0.141.1 and Uvicorn 0.52.4 from the project interpreter. |
| Run backend tests | CSV join, normalization, empty result, API response, and blank-query behavior pass. | All 5 tests passed. |
| Build the Vue frontend | Vite completes a production build without errors. | Build passed; 11 modules were transformed. |
| Open the frontend | The search interface and initial guidance are visible. | Expedia Lite heading, labeled City input, Search button, and guidance were visible. |
| Search `Boston` | T001, T002, T009, and T010 appear. | Four joined rows appeared with those IDs, hotel details, dates, nights, and prices. |
| Search `boston` | Matching ignores capitalization. | The same four trip IDs appeared. |
| Search `Miami` | A clear no-results message appears and the results table is absent. | “No hotel stays found for Miami. Try another city.” appeared; the page contained zero tables. |
| Submit whitespace-only input | The interface asks for a city without showing stale results. | “Enter a city to search for available stays.” appeared; the page contained zero tables. |
| Inspect the browser console | No application warnings or errors. | No warning or error entries were recorded. |

Screenshots: [Boston search results](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/docs/screenshots/part1-boston-results.jpg) and [Miami no-results state](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/docs/screenshots/part1-miami-no-results.jpg).

## Project context and next steps

- [Setup and run instructions](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/README.md)
- [Project-specific agent instructions](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/AGENTS.md)
- [Design pipeline](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/docs/design-pipeline.md)
- [Verification procedure](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/docs/verification.md)
- [Selected setup prompt](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/prompts/01-project-setup.md)
- [Selected Part 1 prompt](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/prompts/02-part-1-search.md)
- [Current handoff](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/handoffs/current.md)

Remaining limitation: Part 1 reads CSV files and does not persist data. The next task is Part 2: seed SQLite once and add booking create, read, cancel, and delete workflows through FastAPI and Vue while preserving this Part 1 checkpoint.
