export const HOTEL_RESULT_LABELS = Object.freeze({
  local: 'Saved locally',
  api: 'API results',
})

export const DEMO_NIGHT_DATES = Object.freeze([
  '2026-10-10',
  '2026-10-11',
  '2026-10-12',
  '2026-10-13',
  '2026-10-14',
])

export class HotelRequestError extends Error {
  constructor(message, { phase, status = 0 } = {}) {
    super(message)
    this.name = 'HotelRequestError'
    this.phase = phase
    this.status = status
  }
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function invalidResponse(phase) {
  const label = phase === 'local' ? 'saved hotel lookup' : 'hotel request'
  return new HotelRequestError(`The ${label} returned an invalid response.`, { phase })
}

async function responseDetail(response, fallback) {
  try {
    const body = await response.json()
    return typeof body.detail === 'string' ? body.detail : fallback
  } catch {
    return fallback
  }
}

async function requestJson(fetchImpl, url, phase, options = {}) {
  let response
  try {
    response = await fetchImpl(url, options)
  } catch {
    throw new HotelRequestError(
      phase === 'local'
        ? 'Saved hotels could not be loaded. Confirm the backend is running and try again.'
        : 'The hotel request could not be completed. Confirm the backend is running and try again.',
      { phase },
    )
  }

  if (!response.ok) {
    const fallback =
      phase === 'local'
        ? 'Saved hotels could not be loaded.'
        : phase === 'save'
          ? 'The hotel could not be saved locally.'
          : phase === 'remove'
            ? 'The saved hotel could not be removed.'
            : 'The live hotel search returned an error.'
    throw new HotelRequestError(await responseDetail(response, fallback), {
      phase,
      status: response.status,
    })
  }

  try {
    return await response.json()
  } catch {
    throw invalidResponse(phase)
  }
}

function validateNight(night, phase) {
  if (
    !isObject(night) ||
    typeof night.date !== 'string' ||
    !Number.isInteger(night.nightly_rate_cents) ||
    !Number.isInteger(night.rooms_available)
  ) {
    throw invalidResponse(phase)
  }
}

function validateSavedHotel(hotel, phase) {
  if (
    !isObject(hotel) ||
    typeof hotel.place_id !== 'string' ||
    !hotel.place_id ||
    typeof hotel.name !== 'string' ||
    typeof hotel.address !== 'string' ||
    !Number.isFinite(hotel.latitude) ||
    !Number.isFinite(hotel.longitude) ||
    !Array.isArray(hotel.searched_zips) ||
    !Array.isArray(hotel.nights) ||
    hotel.nights.length !== DEMO_NIGHT_DATES.length
  ) {
    throw invalidResponse(phase)
  }
  hotel.nights.forEach((night) => validateNight(night, phase))
  if (
    hotel.nights.some(
      (night, index) => night.date !== DEMO_NIGHT_DATES[index],
    )
  ) {
    throw invalidResponse(phase)
  }
  return hotel
}

export function validateSavedLookup(payload, postcode) {
  if (
    !isObject(payload) ||
    payload.zip !== postcode ||
    !Number.isInteger(payload.count) ||
    payload.count < 0 ||
    !Array.isArray(payload.hotels) ||
    payload.count !== payload.hotels.length
  ) {
    throw invalidResponse('local')
  }
  payload.hotels.forEach((hotel) => validateSavedHotel(hotel, 'local'))
  return payload
}

function validateApiLookup(payload) {
  if (
    !isObject(payload) ||
    !isObject(payload.search_center) ||
    !Number.isFinite(payload.search_center.latitude) ||
    !Number.isFinite(payload.search_center.longitude) ||
    typeof payload.search_center.postcode !== 'string' ||
    !Number.isFinite(payload.radius_meters) ||
    !Number.isInteger(payload.count) ||
    payload.count < 0 ||
    !Array.isArray(payload.hotels) ||
    payload.count !== payload.hotels.length
  ) {
    throw invalidResponse('api')
  }
  return payload
}

export async function loadSavedHotels({ apiUrl, postcode, fetchImpl = fetch }) {
  const payload = await requestJson(
    fetchImpl,
    `${apiUrl}/api/saved-hotels?zip=${encodeURIComponent(postcode)}`,
    'local',
    { cache: 'no-store' },
  )
  return validateSavedLookup(payload, postcode)
}

export async function searchHotelsLocalFirst({ apiUrl, postcode, fetchImpl = fetch }) {
  const localPayload = await loadSavedHotels({ apiUrl, postcode, fetchImpl })
  if (localPayload.count > 0) {
    return {
      source: 'local',
      label: HOTEL_RESULT_LABELS.local,
      payload: localPayload,
    }
  }

  const apiPayload = validateApiLookup(
    await requestJson(
      fetchImpl,
      `${apiUrl}/api/hotels?zip=${encodeURIComponent(postcode)}`,
      'api',
    ),
  )
  return {
    source: 'api',
    label: HOTEL_RESULT_LABELS.api,
    payload: apiPayload,
  }
}

export async function saveHotelLocally({ apiUrl, postcode, hotel, fetchImpl = fetch }) {
  const payload = await requestJson(fetchImpl, `${apiUrl}/api/saved-hotels`, 'save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ searched_zip: postcode, hotel }),
  })
  return validateSavedHotel(payload, 'save')
}

export async function removeHotelLocally({ apiUrl, placeId, fetchImpl = fetch }) {
  const payload = await requestJson(
    fetchImpl,
    `${apiUrl}/api/saved-hotels/${encodeURIComponent(placeId)}`,
    'remove',
    { method: 'DELETE' },
  )
  if (!isObject(payload) || payload.place_id !== placeId || payload.deleted !== true) {
    throw invalidResponse('remove')
  }
  return payload
}

export function formatStoredRate(cents) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(cents / 100)
}
