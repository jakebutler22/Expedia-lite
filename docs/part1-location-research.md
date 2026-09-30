# Part 1 live hotel search research and early design

Research started: September 24, 2026
Pre-implementation research completed: September 29, 2026
Implementation and verification completed: September 29, 2026

## Requirement checklist

- [x] Research the Geoapify geocoding and Places requests, response fields,
  Leaflet interaction, map attribution, and failure cases.
- [x] Produce an early list-and-map mockup with all required interface states.
- [x] Accept an exact five-digit U.S. ZIP, preserving a leading zero.
- [x] Resolve that exact ZIP through FastAPI and Geoapify; never substitute a
  different postcode or country.
- [x] Use the resolved coordinates as the center of a Geoapify Places hotel
  search limited to a 5 km circle.
- [x] Return only normalized API data to Vue; do not invent price, rating,
  availability, booking data, or missing fields.
- [x] Show the returned hotels in a list and Leaflet map with one shared
  selected-hotel identity.
- [x] Keep map attribution visible and all applicable controls keyboard usable.
- [x] Load `GEOAPIFY_API_KEY` from ignored `backend/.env` and add a safe,
  committed `backend/.env.example` with no credential value.
- [x] Verify loading, results, invalid ZIP, unresolved ZIP, zero-result, and
  failed-request states independently.
- [x] Capture verification evidence, record the demo, and complete `report.md`.

## Geoapify request design

### 1. Resolve and confirm the requested ZIP

Geoapify's Forward Geocoding API accepts `GET` requests at
`https://api.geoapify.com/v1/geocode/search`. The backend should send the ZIP
as the structured `postcode` parameter with `type=postcode`,
`filter=countrycode:us`, `format=json`, and a bounded `limit`.

The returned result is usable only when its postcode exactly equals the
requested five-character string, its country code is `us`, and its latitude
and longitude are finite and in range. This explicit confirmation prevents a
provider's approximate result from silently replacing an unresolved ZIP.
The ZIP remains a string at every layer so a value such as `02108` keeps its
leading zero.

Source: [Geoapify Geocoding API](https://apidocs.geoapify.com/docs/geocoding/)

### 2. Search for hotels within 5 km

After a ZIP is confirmed, FastAPI should call
`https://api.geoapify.com/v2/places` with:

```text
categories=accommodation.hotel
filter=circle:{longitude},{latitude},5000
bias=proximity:{longitude},{latitude}
limit=20
```

The `filter` is the hard 5,000-metre boundary. The `bias` only orders the
filtered results by proximity and must not replace the filter. Geoapify's
documented default is 20 results; setting `limit=20` makes the intended bound
explicit without implying that the response is a complete hotel inventory.

The response is a GeoJSON `FeatureCollection`. Its documented place fields
include `name`, address components, `formatted`, `lat`, `lon`, `distance`,
`categories`, and `place_id`. The backend may normalize those fields, but it
must omit absent optional data rather than synthesize values. `place_id` is the
preferred list/map selection key; coordinates come from the feature response.

Source: [Geoapify Places API](https://apidocs.geoapify.com/docs/places/)

### 3. Keep the credential on the server

Vue should call Expedia Lite's FastAPI route only. Both Geoapify requests are
made by the backend with `GEOAPIFY_API_KEY` loaded from `backend/.env`. The key
must not appear in frontend source, browser requests, API response models,
screenshots, logs, or committed files.

Implementation result: `backend/app/config.py` loads ignored `backend/.env`,
and the trackable `backend/.env.example` contains only a placeholder. The real
credential was not read, displayed, copied into documentation, or exposed to
the frontend.

## Map and interaction research

Leaflet 1.9.4 provides keyboard navigation for the map and makes markers
keyboard focusable and activatable with Enter by default. Markers should also
receive API-derived `title` and `alt` text. Leaflet's attribution control is
enabled by default and automatically gathers attribution from map layers.

Source: [Leaflet 1.9.4 reference](https://leafletjs.com/reference.html)

The planned base layer is the standard OpenStreetMap raster endpoint,
`https://tile.openstreetmap.org/{z}/{x}/{y}.png`. Its policy requires visible
`© OpenStreetMap contributors` attribution and forbids bulk download or tile
prefetching. Expedia Lite will use normal interactive browser viewing and will
not hide the attribution control.

Source: [OpenStreetMap tile usage policy](https://operations.osmfoundation.org/policies/tiles/)

List rows should be native buttons. A list button and its Leaflet marker both
set one `selectedPlaceId`; the view derives the selected row, marker styling,
popup, and detail text from that single state. This avoids maintaining two
independent selections that can drift apart.

## Relevant interface and interaction patterns

### Google Maps place search pattern

Google's Place Search example combines an explicit text field and Search
button with a selectable place list and markers. Its example uses the same
place identifier to connect a list selection to the corresponding marker,
clears stale markers before a new search, and fits the map to returned places.
Google's marker accessibility guidance also makes marker names available to
screen readers and supports keyboard activation.

Useful pattern: treat list rows and markers as two controls for the same place,
not as separate datasets. Keep explicit Search and Enter-key submission.

Weakness for this assignment: the example is success-oriented and does not
define invalid-input, unresolved-location, zero-result, timeout, or provider
failure states. It also uses Google-specific components that Expedia Lite does
not need.

Sources:

- [Google Maps Place Search element](https://developers.google.com/maps/documentation/javascript/places-ui-kit/place-search)
- [Google Maps accessible markers](https://developers.google.com/maps/documentation/javascript/advanced-markers/accessible-markers)

### Airbnb stay-search map pattern

Airbnb's stay-search documentation describes using a map to understand the
geographic distribution of matching stays and to show nearby points of
interest. This validates the value of keeping the list and map visible in the
same results workflow.

Useful pattern: a map supplies location context while the list remains the
readable, scannable representation of the returned places.

Weakness for this assignment: Airbnb states that map results may differ from
list results, and its ranking can use personalization, popularity, price, and
availability. Expedia Lite must do the opposite: one API collection powers
both views, selection must match exactly, and unavailable commercial fields
must not be shown or inferred.

Sources:

- [Airbnb: How search results work](https://www.airbnb.com/help/article/39)
- [Airbnb: Searching for stays](https://www.airbnb.com/help/article/252)

## Useful patterns observed

- Keep the search action explicit and allow Enter to submit the same form.
- Pair a scannable result list with a larger map for spatial context.
- Use one provider identifier to synchronize list selection, marker selection,
  selected styling, and popup/detail content.
- Fit the map to returned markers while preserving the resolved ZIP as the
  documented search center and the 5 km circle as the hard query boundary.
- Keep result status, selected state, and errors in predictable live regions;
  do not depend on marker color or hover alone.

## Weaknesses and omissions observed

- Geoapify documents request and response behavior, but not the product-level
  distinction between invalid ZIP, unresolved ZIP, empty Places results, and
  upstream failure; Expedia Lite must define those states.
- Leaflet supplies map and marker mechanics, but application code must own the
  shared selection state and keep it synchronized with Vue.
- Google examples do not demonstrate the complete failure-state matrix needed
  for this assignment.
- Airbnb intentionally permits different map/list result sets and commercial
  ranking signals, which conflicts with the assignment's single-result-set and
  no-invented-data rules.
- Marker-only results are insufficient for keyboard and screen-reader users;
  the list remains a full alternative way to inspect and select every hotel.

## Specific design decisions for Expedia Lite

1. Use a text input with a five-ASCII-digit constraint so leading zeroes are
   preserved; repeat validation in FastAPI as the authority.
2. Let one FastAPI request orchestrate exact U.S. postcode confirmation and
   the subsequent Geoapify Places query. Vue never calls Geoapify directly.
3. Use `accommodation.hotel`, a 5,000-metre circle filter, and proximity bias
   around the confirmed coordinates. Never replace the requested ZIP.
4. Normalize only API-returned identifiers, names, address parts, coordinates,
   categories, and distance. Omit absent optional values and never add prices,
   ratings, availability, or booking claims.
5. Render the same normalized hotel array in the list and Leaflet map. Store
   only one `selectedPlaceId`; list and marker actions update that value.
6. Keep Leaflet and OpenStreetMap attribution visible. Keep search, list rows,
   markers, and zoom controls keyboard usable with descriptive accessible text.
7. Render ready, loading, results, invalid ZIP, unresolved ZIP, zero nearby
   results, and failed request as distinct states.
8. Preserve MVC: provider/configuration and normalization in backend services,
   HTTP orchestration in FastAPI routes, and rendering/selection in Vue.

## Distinct interface states

- **Ready:** labeled ZIP text input and Search button; no result claim yet.
- **Loading:** announce the ZIP being searched and prevent duplicate submits.
- **Results:** identify the confirmed ZIP/search center and show the same API
  hotels in the list and map.
- **Invalid ZIP:** explain that exactly five ASCII digits are required.
- **Unresolved ZIP:** say the requested ZIP could not be resolved; retain the
  requested value and do not show a replacement location.
- **Zero nearby results:** confirm the resolved ZIP but state that Geoapify
  returned no hotels inside 5 km.
- **Failed request:** show a safe service/network message distinct from invalid
  or unresolved input, with retry available.

Status changes and the selected hotel need an `aria-live` region. The search
form submits with Enter, list items and markers are keyboard activatable, zoom
controls remain available, focus is visible, and map/list meaning is never
communicated by color alone.

## MVC responsibility boundary

| Layer | Part 1 responsibility |
| --- | --- |
| Model/service | Validate and normalize ZIP and Places data; read backend configuration; call Geoapify; reject malformed responses. |
| Controller | Expose one FastAPI search route and translate validation, unresolved, provider, and timeout outcomes into safe HTTP responses. |
| View | Submit the ZIP to FastAPI, render the seven UI states, render Leaflet, and synchronize list/map selection by `place_id`. |

The view does not call Geoapify, interpret provider credentials, invent hotel
fields, or decide whether a provider result matches the requested ZIP.

## Early layout sketch

```text
+-----------------------------------------------------------------------+
| Expedia Lite                         Live hotel search                 |
| Find hotels near a U.S. ZIP                                           |
| U.S. ZIP code [ 02108 ] [ Search hotels ]                             |
+-------------------------------+---------------------------------------+
| Hotels within 5 km            | Leaflet map centered on resolved ZIP |
|                               |                                       |
| [1] {API hotel name}          |       (1)                             |
|     {API formatted address}   |                    (2)                |
|     {API distance, if present}|         (+) (-)                       |
|                               |                                       |
| [2] {API hotel name}          |       Selected: same place_id         |
|     {API formatted address}   |       © OpenStreetMap contributors   |
+-------------------------------+---------------------------------------+
```

This sketch uses field labels rather than fictional hotel facts. The companion
interactive mockup at `docs/part1-live-hotel-search-mockup.html` previews list
and marker selection plus each required state; it makes no network request and
contains no API credential.

## Dependency checkpoint

The existing frontend had no mapping library. After approval, only
`leaflet@1.9.4` was added. The installed package and lockfile resolve to 1.9.4,
and the unchanged frontend production build still passes. No other dependency
was added.
