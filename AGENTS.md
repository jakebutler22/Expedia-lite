# Project instructions

Work only inside this folder. Read the project before editing. Ask before installing dependencies. Review and test before committing.

## Scope and architecture

- Keep the application name **Expedia Lite** consistent in the interface and documentation.
- Keep Vue code in `frontend/` and Python/FastAPI code in `backend/`.
- Preserve the tagged Part 1 checkpoint. In Part 2, seed SQLite once from the four supplied CSV files; after seeding, SQLite is the source of truth and request paths must not read the CSV files.
- Treat the supplied CSV files as immutable one-time seed data. Restarting must not duplicate starter rows, restore deleted bookings, or erase bookings created by a user.
- Keep cancellation and deletion distinct: cancellation updates a booking to `cancelled` and retains the record, while deletion permanently removes the booking.
- Keep project context in `README.md`, `docs/`, `prompts/`, and `handoffs/current.md` current with the code.

## Dependency loop

Use CHECK → TAKE ACTION → VERIFY: inspect the relevant runtime and installed packages, describe the smallest required installation, install only after approval, then verify versions or imports in the target environment.

## AutoLoop

Run the agreed check → inspect any failure → make the smallest in-scope fix → rerun the check. Stop when it passes, after five correction cycles, or when extra permission is needed. Report what passed and what remains unverified.

## SmokeTest

SmokeTest verifies without editing code or dependencies. Run this sequence:

1. Confirm the backend test suite and frontend production build pass.
2. Search a hotel name from the supplied data and confirm that hotel's stays appear.
3. Search a city and confirm its expected trips still appear.
4. Search for a value matching nothing and confirm a clear no-results message appears with no results table.
5. Create a new booking through the browser and confirm it appears in the selected traveler's history.
6. Cancel that booking through the browser and confirm it remains in history with a cancelled status.
7. Delete a test booking through the browser and confirm it disappears from history.
8. Refresh the browser and confirm the new booking remains, the cancelled booking remains cancelled, and the deleted booking remains absent.
9. Fully stop and restart both backend and frontend processes started for the test. Confirm the new booking is present, the cancelled booking is still cancelled, and the deleted booking has not returned.
10. Confirm the supplied starter records were not duplicated after the restart.
11. Confirm the browser console contains no application warnings or errors.

During the run, save full-page screenshots in `docs/screenshots/` as `part2-<name>.jpg` after creating the booking, cancelling it, deleting the test booking, and completing the full restart. Frame each screenshot so every booking row and the status column are legible. The restart screenshot is the persistence evidence.

Never stop an unrelated process. Stop only backend and frontend processes started by the current SmokeTest run.
