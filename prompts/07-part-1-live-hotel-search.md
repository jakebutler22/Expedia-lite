# Selected prompt — Assignment 2.1 Part 1 implementation and verification

## Purpose

Implement the researched and mocked-up live hotel search inside the existing
Expedia Lite FastAPI + Vue repository without replacing the working SQLite
booking feature.

## Constraints supplied for the work

- Validate exactly five numeric U.S. ZIP digits while preserving leading zeroes.
- Call Geoapify geocoding and Places only from FastAPI; confirm an exact U.S.
  postcode before using its returned coordinate as the center of a 5 km hotel
  query.
- Never substitute another location for an unresolved ZIP.
- Return and display only real available provider fields; do not invent price,
  rating, availability, rooms, or booking information.
- Distinguish loading, results, invalid, unresolved, zero-result, and failed
  request states.
- Render one result dataset in a Vue list and Leaflet map, with selection
  synchronized in both directions, appropriate framing, visible attribution,
  and basic keyboard use.
- Keep the Geoapify key in ignored backend configuration and out of frontend
  assets and Git.
- Preserve MVC responsibilities and all existing behavior. Do not add Part 2
  shortlist/database work.
- Follow AGENTS.md CHECK → TAKE ACTION → VERIFY. Inspect before adding a
  dependency and do not install anything without approval.

## Recorded execution outcome

CHECK found the previously approved exact `leaflet@1.9.4` plus all Python and
Vue dependencies already installed. TAKE ACTION installed nothing. The work
added isolated geocoding/orchestration/Places services, normalized response
models and a FastAPI route, focused backend tests, the synchronized accessible
Vue list/map UI, backend-only environment configuration, and updated project
documentation. VERIFY ran the full backend suite, Vite production build, live
Geoapify requests, browser state/selection/error checks, attribution review,
preserved sample-stay search, and browser console inspection.

No API key or provider response containing the key is recorded in this file.

## Required AI evidence — failed and revised approach

During the September 29, 2026 full browser verification, the initial Leaflet
marker implementation proved incomplete for keyboard users. Pressing Enter on
the XV Beacon marker opened Leaflet's popup, but the matching Vue list row and
the marker's shared selected state did not change. The implementation had
listened only for the marker `click` event; Leaflet handles keyboard popup
activation through a separate `keypress` event.

The approach was revised by adding an Enter-only `keypress` listener that calls
the same `selectLiveHotel(place_id, 'marker')` function as pointer selection.
The affected browser test was rerun: XV Beacon became selected in both the map
and list, its popup opened, and both controls exposed the selected state. The
production build and full backend suite then passed. This is a real failed and
corrected verification path, not a hypothetical example.
