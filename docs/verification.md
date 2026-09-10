# Part 1 verification

Use CHECK → TAKE ACTION → VERIFY for dependencies. Once setup is complete, run AutoLoop with the commands and browser checks below.

## Automated checks

From the project root:

```bash
backend/.venv/bin/python -m pytest backend/tests
npm --prefix frontend run build
```

Expected: all backend tests pass and Vite completes a production build without errors.

## Browser SmokeTest

Start the API and frontend as described in `README.md`, then check:

| Action | Expected result |
| --- | --- |
| Open the frontend | Expedia Lite heading, city input, Search button, and initial guidance are visible. |
| Search `Boston` | Four rows appear for T001, T002, T009, and T010. |
| Search `boston` | The same four rows appear, demonstrating case-insensitive search. |
| Search `Miami` | The table is absent and a clear no-results message names Miami. |
| Submit an empty city | The table is absent and the page asks for a city. |

## Manual source review

Before committing, inspect every changed file in VS Code Source Control. Confirm the backend is the only layer that reads CSVs, the two files join on `hotel_id`, the frontend calls FastAPI, all table columns have clear headings, and no SQLite/CRUD work has entered Part 1.

## Recorded observations

Verified on September 9-10, 2026 with Python 3.14.7, FastAPI 0.141.1, Uvicorn 0.52.4, Node 24.12.0, npm 11.6.2, Vue 3.5.42, and Vite 8.2.2.

| Check | Observed result | Status |
| --- | --- | --- |
| Manual VS Code Source Control review | Completed a file-by-file Source Control review. Confirmed `backend/app/search.py` is the only layer reading CSVs and joins hotels to trips on `hotel_id`; `frontend/src/App.vue` calls the FastAPI endpoint and supplies headings for all eight table columns; no SQLite or booking CRUD code is present. | Pass |
| CHECK → TAKE ACTION → VERIFY dependency cycle | CHECK used Python 3.14.7 at `backend/.venv/bin/python`, Node v24.12.0, and npm 11.6.2; FastAPI/Uvicorn and the project-local Vue packages required installation. TAKE ACTION installed `backend/requirements.txt` into `backend/.venv` and the frontend packages into `frontend/node_modules`. VERIFY reran the version commands and successfully imported FastAPI 0.141.1 and Uvicorn 0.52.4 from the project interpreter. | Pass |
| Backend pytest suite | 5 tests passed. | Pass |
| Frontend production build | Vite transformed 11 modules and completed the build. | Pass |
| Initial page | Heading, labeled city input, Search button, and guidance were visible. | Pass |
| `Boston` | Four rows appeared: T001, T002, T009, and T010, with joined hotel details and calculated prices. | Pass |
| `boston` | The same four trip IDs appeared. | Pass |
| `Miami` | “No hotel stays found for Miami. Try another city.” appeared; zero tables remained. | Pass |
| Whitespace-only city | “Enter a city to search for available stays.” appeared; zero tables remained. | Pass |
| Browser console | No warning or error entries were recorded. | Pass |

Evidence: [Boston results](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/docs/screenshots/part1-boston-results.jpg) and [Miami no-results state](https://github.com/jakebutler22/Expedia-lite/blob/part1-submission/docs/screenshots/part1-miami-no-results.jpg).
