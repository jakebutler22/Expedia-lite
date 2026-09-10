# Project instructions

Work only inside this folder. Read the project before editing. Ask before installing dependencies. Review and test before committing.

## Scope and architecture

- Keep the application name **Expedia Lite** consistent in the interface and documentation.
- Keep Vue code in `frontend/` and Python/FastAPI code in `backend/`.
- In Part 1, use `backend/data/hotels.csv` and `backend/data/trips.csv` as the source of truth. Join them with `hotel_id`.
- Do not add Part 2 SQLite or booking CRUD behavior to the Part 1 checkpoint.
- Keep project context in `README.md`, `docs/`, `prompts/`, and `handoffs/current.md` current with the code.

## Dependency loop

Use CHECK → TAKE ACTION → VERIFY: inspect the relevant runtime and installed packages, describe the smallest required installation, install only after approval, then verify versions or imports in the target environment.

## AutoLoop

Run the agreed check → inspect any failure → make the smallest in-scope fix → rerun the check. Stop when it passes, after five correction cycles, or when extra permission is needed. Report what passed and what remains unverified.

## SmokeTest

SmokeTest checks without editing code. Run backend tests and the frontend production build, start both applications, then operate the browser:

1. Search for `Boston`; confirm four rows with trip IDs T001, T002, T009, and T010.
2. Search for lowercase `boston`; confirm the same four rows.
3. Search for `Miami`; confirm a clear no-results message and no results table.
4. Submit an empty city; confirm the interface asks for a city and makes no useful search claim.
