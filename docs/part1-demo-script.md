# Assignment 2.1 Part 1 demo script

This is the production-demo artifact for **Expedia Lite — Live Hotel Search
and Map**. It is intentionally limited to Assignment 2.1 Part 1. The existing
sample-stay/booking interface lower on the same page predates this assignment
and is not part of this demo.

## Preparation

1. Confirm `GEOAPIFY_API_KEY` is configured in ignored `backend/.env`. Never
   open or display that file while recording.
2. From the repository root, start FastAPI:

   ```bash
   backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --port 8000
   ```

3. In a second terminal, start Vue:

   ```bash
   npm --prefix frontend run dev
   ```

4. Open `http://127.0.0.1:5173` and position the **Live Geoapify search**
   section in the recording frame. Keep the map attribution visible.

## Three-to-four-minute walkthrough

1. **Introduce the boundary.** Explain that Vue calls FastAPI, FastAPI calls
   Geoapify, and the browser never receives the API key.
2. **Leading-zero success.** Focus the ZIP field, enter `02108`, and press
   Enter. Point out the announced loading state, confirmed `02108` result,
   dynamic result count, 5 km search radius, ZIP center, provider-derived hotel
   list, numbered markers, and visible Leaflet/OpenStreetMap attribution. Do
   not promise a particular count because Geoapify data can change.
3. **List-to-map synchronization.** Use Tab to focus a different list result
   and press Enter. Show that the matching marker becomes selected and its
   popup opens.
4. **Map-to-list synchronization.** Tab to a different named marker and press
   Enter. Show that its matching list row and marker now share the selected
   state.
5. **Honest states.** Search `1680` to show **Invalid ZIP**, `00000` to show
   **ZIP not resolved** without a substitute location, and `99999` to show the
   dated zero-nearby-result example if Geoapify still returns an empty hotel
   collection. If live provider data changes, use another confirmed zero-result
   ZIP from the current verification pass and state the observation date.
6. **Close with data integrity.** Explain that hotel names, locations,
   coordinates, and optional distances come from the API response, and the
   live feature intentionally invents no price, rating, room availability, or
   booking information.

## Exact recording step when a video is required

On macOS, press **Shift-Command-5**, choose **Record Selected Portion**, frame
the browser around the live-search section, select **Record**, perform the
walkthrough above, then stop from the menu-bar recording control. Save the file
as `part1-live-hotel-search-demo.mov`. Do not include `backend/.env`, terminal
environment output, or any credential-bearing screen in the recording.

The repository's dated, non-video demonstration evidence is
[part1-verification-2026-09-29.md](part1-verification-2026-09-29.md).
