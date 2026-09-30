<script setup>
import L from 'leaflet'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import 'leaflet/dist/leaflet.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const query = ref('')
const searchedQuery = ref('')
const stays = ref([])
const loading = ref(false)
const message = ref('')
const error = ref('')

const travelers = ref([])
const selectedUserId = ref('')
const travelersLoading = ref(false)
const travelersError = ref('')
const bookingHistory = ref([])
const historyLoading = ref(false)
const historyError = ref('')
const bookingAction = ref('')
const bookingFeedback = ref('')
const bookingFeedbackType = ref('success')
const deleteCandidateId = ref('')

const zipCode = ref('')
const requestedZip = ref('')
const hotelSearch = ref(null)
const hotelSearchState = ref('ready')
const hotelSearchError = ref('')
const selectedHotelId = ref('')
const hotelMapElement = ref(null)

const hotelListButtons = new Map()
const hotelMarkers = new Map()
let hotelMap = null

const selectedTraveler = computed(() =>
  travelers.value.find((traveler) => traveler.user_id === selectedUserId.value),
)

const liveHotels = computed(() => hotelSearch.value?.hotels || [])
const liveSearchLoading = computed(() => hotelSearchState.value === 'loading')

const resultSummary = computed(() => {
  if (!searchedQuery.value || loading.value || error.value || message.value) {
    return ''
  }

  const count = stays.value.length
  return `${count} ${count === 1 ? 'stay' : 'stays'} matching ${searchedQuery.value}`
})

const formatCurrency = (amount) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount)

const formatDate = (value) =>
  new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${value}T00:00:00Z`))

async function getErrorMessage(response, fallback) {
  try {
    const body = await response.json()
    return typeof body.detail === 'string' ? body.detail : fallback
  } catch {
    return fallback
  }
}

function displayHotelLocation(hotel) {
  if (hotel.formatted_address) {
    return hotel.formatted_address
  }

  const addressLines = [hotel.address_line1, hotel.address_line2].filter(Boolean)
  if (addressLines.length) {
    return addressLines.join(', ')
  }

  const locality = [hotel.city, hotel.state, hotel.postcode, hotel.country].filter(Boolean)
  if (locality.length) {
    return locality.join(', ')
  }

  return `${hotel.latitude.toFixed(5)}, ${hotel.longitude.toFixed(5)}`
}

function formatHotelDistance(distanceMeters) {
  if (typeof distanceMeters !== 'number') {
    return ''
  }
  if (distanceMeters < 1000) {
    return `${Math.round(distanceMeters)} m from search center`
  }
  return `${(distanceMeters / 1000).toFixed(1)} km from search center`
}

function displaySearchCenter(center) {
  if (center.locality) {
    return center.locality
  }
  return `${center.latitude.toFixed(5)}, ${center.longitude.toFixed(5)}`
}

function setHotelListButton(placeId, element) {
  if (element) {
    hotelListButtons.set(placeId, element)
  } else {
    hotelListButtons.delete(placeId)
  }
}

function destroyHotelMap() {
  if (hotelMap) {
    hotelMap.remove()
    hotelMap = null
  }
  hotelMarkers.clear()
}

function updateMarkerSelection() {
  hotelMarkers.forEach(({ marker }, placeId) => {
    const isSelected = placeId === selectedHotelId.value
    marker.getElement()?.classList.toggle('is-selected', isSelected)
    marker.getElement()?.setAttribute('aria-pressed', String(isSelected))
    marker.setZIndexOffset(isSelected ? 1000 : 0)
  })
}

function createHotelPopup(hotel) {
  const popup = document.createElement('div')
  popup.className = 'live-hotel-popup'

  const name = document.createElement('strong')
  name.textContent = hotel.name
  popup.append(name)

  const location = document.createElement('span')
  location.textContent = displayHotelLocation(hotel)
  popup.append(location)

  return popup
}

function selectLiveHotel(placeId, source) {
  const hotel = liveHotels.value.find((candidate) => candidate.place_id === placeId)
  if (!hotel) {
    return
  }

  selectedHotelId.value = placeId
  updateMarkerSelection()

  const markerRecord = hotelMarkers.get(placeId)
  if (markerRecord) {
    markerRecord.marker.openPopup()
    if (source === 'list') {
      hotelMap?.panTo(markerRecord.marker.getLatLng())
    }
  }

  if (source === 'marker') {
    hotelListButtons.get(placeId)?.scrollIntoView({ block: 'nearest' })
  }
}

function renderHotelMap() {
  if (!hotelMapElement.value || !hotelSearch.value) {
    return
  }

  destroyHotelMap()
  const center = L.latLng(
    hotelSearch.value.search_center.latitude,
    hotelSearch.value.search_center.longitude,
  )
  hotelMap = L.map(hotelMapElement.value, {
    attributionControl: true,
    keyboard: true,
    zoomControl: true,
  })

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(hotelMap)

  L.circle(center, {
    radius: hotelSearch.value.radius_meters,
    color: '#3150d8',
    fillColor: '#6f86eb',
    fillOpacity: 0.08,
    interactive: false,
    weight: 2,
  }).addTo(hotelMap)

  L.circleMarker(center, {
    radius: 6,
    color: '#151f4a',
    fillColor: '#ffd500',
    fillOpacity: 1,
    interactive: false,
    weight: 3,
  })
    .bindTooltip(`Search center for ZIP ${hotelSearch.value.search_center.postcode}`)
    .addTo(hotelMap)

  const bounds = L.latLngBounds([center])
  liveHotels.value.forEach((hotel, index) => {
    const marker = L.marker([hotel.latitude, hotel.longitude], {
      alt: `${hotel.name} map marker`,
      icon: L.divIcon({
        className: 'live-hotel-marker-wrapper',
        html: `<span class="live-hotel-marker" aria-hidden="true">${index + 1}</span>`,
        iconAnchor: [19, 19],
        iconSize: [38, 38],
        popupAnchor: [0, -21],
      }),
      keyboard: true,
      riseOnHover: true,
      title: hotel.name,
    })
      .bindPopup(createHotelPopup(hotel))
      .on('click', () => selectLiveHotel(hotel.place_id, 'marker'))
      .on('keypress', (event) => {
        if (event.originalEvent?.key === 'Enter' || event.originalEvent?.keyCode === 13) {
          selectLiveHotel(hotel.place_id, 'marker')
        }
      })
      .addTo(hotelMap)

    hotelMarkers.set(hotel.place_id, { marker })
    bounds.extend([hotel.latitude, hotel.longitude])
  })

  if (liveHotels.value.length) {
    hotelMap.fitBounds(bounds, { maxZoom: 15, padding: [42, 42] })
  } else {
    hotelMap.setView(center, 13)
  }

  updateMarkerSelection()
  const selectedMarker = hotelMarkers.get(selectedHotelId.value)?.marker
  selectedMarker?.openPopup()
  window.requestAnimationFrame(() => hotelMap?.invalidateSize())
}

function setBookingFeedback(text, type = 'success') {
  bookingFeedback.value = text
  bookingFeedbackType.value = type
}

async function search() {
  const searchTerm = query.value.trim()
  stays.value = []
  searchedQuery.value = ''
  message.value = ''
  error.value = ''

  if (!searchTerm) {
    message.value = 'Enter a hotel name or city to search for available stays.'
    return
  }

  loading.value = true
  try {
    const response = await fetch(`${API_URL}/api/stays?query=${encodeURIComponent(searchTerm)}`)
    if (!response.ok) {
      throw new Error(await getErrorMessage(response, 'The search service returned an error.'))
    }

    const data = await response.json()
    stays.value = data.stays
    searchedQuery.value = data.query

    if (data.count === 0) {
      message.value = `No hotel stays found for ${data.query}. Try another hotel name or city.`
    }
  } catch (requestError) {
    error.value =
      requestError.message ||
      'We could not complete the search. Confirm the backend is running and try again.'
  } finally {
    loading.value = false
  }
}

async function searchLiveHotels() {
  const postcode = zipCode.value.trim()
  destroyHotelMap()
  hotelListButtons.clear()
  hotelSearch.value = null
  selectedHotelId.value = ''
  hotelSearchError.value = ''

  if (!/^[0-9]{5}$/.test(postcode)) {
    hotelSearchState.value = 'invalid'
    hotelSearchError.value = 'Enter exactly five numeric digits, including a leading zero when needed.'
    return
  }

  requestedZip.value = postcode
  hotelSearchState.value = 'loading'

  try {
    const response = await fetch(
      `${API_URL}/api/hotels?zip=${encodeURIComponent(postcode)}`,
    )
    if (!response.ok) {
      const detail = await getErrorMessage(response, 'The live hotel search returned an error.')
      if (response.status === 400) {
        hotelSearchState.value = 'invalid'
      } else if (response.status === 404) {
        hotelSearchState.value = 'unresolved'
      } else {
        hotelSearchState.value = 'failed'
      }
      hotelSearchError.value = detail
      return
    }

    hotelSearch.value = await response.json()
    selectedHotelId.value = hotelSearch.value.hotels[0]?.place_id || ''
    hotelSearchState.value = hotelSearch.value.count === 0 ? 'empty' : 'results'
    await nextTick()
    renderHotelMap()
  } catch {
    hotelSearchState.value = 'failed'
    hotelSearchError.value =
      'We could not complete the live hotel search. Confirm the backend is running and try again.'
  }
}

async function loadBookingHistory() {
  if (!selectedUserId.value) {
    bookingHistory.value = []
    return
  }

  const requestedUserId = selectedUserId.value
  historyLoading.value = true
  historyError.value = ''
  deleteCandidateId.value = ''

  try {
    const response = await fetch(
      `${API_URL}/api/users/${encodeURIComponent(requestedUserId)}/bookings`,
    )
    if (!response.ok) {
      throw new Error(await getErrorMessage(response, 'Booking history could not be loaded.'))
    }

    const data = await response.json()
    if (selectedUserId.value === requestedUserId) {
      bookingHistory.value = data.bookings
    }
  } catch (requestError) {
    if (selectedUserId.value === requestedUserId) {
      bookingHistory.value = []
      historyError.value = requestError.message || 'Booking history could not be loaded.'
    }
  } finally {
    if (selectedUserId.value === requestedUserId) {
      historyLoading.value = false
    }
  }
}

async function loadTravelers() {
  travelersLoading.value = true
  travelersError.value = ''

  try {
    const response = await fetch(`${API_URL}/api/users`)
    if (!response.ok) {
      throw new Error(await getErrorMessage(response, 'Demo travelers could not be loaded.'))
    }

    travelers.value = await response.json()
    if (travelers.value.length) {
      selectedUserId.value = travelers.value[0].user_id
      await loadBookingHistory()
    }
  } catch (requestError) {
    travelersError.value = requestError.message || 'Demo travelers could not be loaded.'
  } finally {
    travelersLoading.value = false
  }
}

async function changeTraveler() {
  setBookingFeedback('')
  await loadBookingHistory()
}

async function createStayBooking(stay) {
  if (!selectedTraveler.value) {
    setBookingFeedback('Select a demo traveler before booking a stay.', 'error')
    return
  }

  const traveler = selectedTraveler.value
  bookingAction.value = `create:${stay.trip_id}`
  setBookingFeedback('')

  try {
    const response = await fetch(`${API_URL}/api/bookings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: traveler.user_id, trip_id: stay.trip_id }),
    })
    if (!response.ok) {
      throw new Error(await getErrorMessage(response, 'The booking could not be created.'))
    }

    const createdBooking = await response.json()
    if (selectedUserId.value === traveler.user_id) {
      await loadBookingHistory()
    }
    setBookingFeedback(
      `${createdBooking.booking_id} was booked for ${traveler.display_name} and added to booking history.`,
    )
  } catch (requestError) {
    setBookingFeedback(requestError.message || 'The booking could not be created.', 'error')
  } finally {
    bookingAction.value = ''
  }
}

async function cancelHistoryBooking(booking) {
  bookingAction.value = `cancel:${booking.booking_id}`
  deleteCandidateId.value = ''
  setBookingFeedback('')

  try {
    const response = await fetch(
      `${API_URL}/api/bookings/${encodeURIComponent(booking.booking_id)}/cancel`,
      { method: 'PATCH' },
    )
    if (!response.ok) {
      throw new Error(await getErrorMessage(response, 'The booking could not be cancelled.'))
    }

    const cancelledBooking = await response.json()
    bookingHistory.value = bookingHistory.value.map((historyBooking) =>
      historyBooking.booking_id === cancelledBooking.booking_id
        ? cancelledBooking
        : historyBooking,
    )
    setBookingFeedback(
      `${cancelledBooking.booking_id} is cancelled and remains visible in booking history.`,
    )
  } catch (requestError) {
    setBookingFeedback(requestError.message || 'The booking could not be cancelled.', 'error')
  } finally {
    bookingAction.value = ''
  }
}

function requestDelete(bookingId) {
  deleteCandidateId.value = bookingId
  setBookingFeedback('')
}

async function deleteHistoryBooking(booking) {
  bookingAction.value = `delete:${booking.booking_id}`
  setBookingFeedback('')

  try {
    const response = await fetch(
      `${API_URL}/api/bookings/${encodeURIComponent(booking.booking_id)}`,
      { method: 'DELETE' },
    )
    if (!response.ok) {
      throw new Error(await getErrorMessage(response, 'The booking could not be deleted.'))
    }

    bookingHistory.value = bookingHistory.value.filter(
      (historyBooking) => historyBooking.booking_id !== booking.booking_id,
    )
    deleteCandidateId.value = ''
    setBookingFeedback(`${booking.booking_id} was permanently deleted from booking history.`)
  } catch (requestError) {
    setBookingFeedback(requestError.message || 'The booking could not be deleted.', 'error')
  } finally {
    bookingAction.value = ''
  }
}

onMounted(loadTravelers)
onBeforeUnmount(destroyHotelMap)
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <a class="brand" href="#" aria-label="Expedia Lite home">
        <span class="brand-mark" aria-hidden="true">↗</span>
        <span>Expedia Lite</span>
      </a>
      <span class="course-label">Hotel search and booking</span>
    </header>

    <main>
      <section class="hero" aria-labelledby="page-title">
        <p class="eyebrow">Find your next stay</p>
        <h1 id="page-title">Where are you going?</h1>
        <p class="intro">
          Search our sample stays by hotel name or city, then book a trip for a demo traveler.
        </p>

        <form class="search-card" @submit.prevent="search">
          <label for="search-query">Hotel name or city</label>
          <div class="search-row">
            <div class="input-wrap">
              <span aria-hidden="true">⌖</span>
              <input
                id="search-query"
                v-model="query"
                name="query"
                type="text"
                autocomplete="off"
                placeholder="Try Harbor Lantern Hotel or Boston"
              />
            </div>
            <button type="submit" :disabled="loading">
              {{ loading ? 'Searching…' : 'Search' }}
            </button>
          </div>
          <p class="city-hints">Hotel names can be partial, such as Harbor.</p>
        </form>
      </section>

      <section class="live-search" aria-labelledby="live-search-title">
        <div class="live-search-heading">
          <div>
            <p class="eyebrow">Live Geoapify search</p>
            <h2 id="live-search-title">Hotels within 5 km of a U.S. ZIP</h2>
          </div>
          <p>
            The backend confirms the requested postcode and returns nearby provider results without
            exposing the Geoapify credential.
          </p>
        </div>

        <form class="live-search-form" novalidate @submit.prevent="searchLiveHotels">
          <label for="zip-code">Five-digit U.S. ZIP code</label>
          <div class="live-search-row">
            <div class="input-wrap">
              <span aria-hidden="true">⌖</span>
              <input
                id="zip-code"
                v-model="zipCode"
                name="zip"
                type="text"
                inputmode="numeric"
                autocomplete="postal-code"
                pattern="[0-9]{5}"
                maxlength="5"
                placeholder="02108"
                :disabled="liveSearchLoading"
              />
            </div>
            <button type="submit" :disabled="liveSearchLoading">
              {{ liveSearchLoading ? 'Searching…' : 'Search live hotels' }}
            </button>
          </div>
          <p class="live-search-help">Leading zeros are preserved, such as 02108 for Boston.</p>
        </form>

        <div class="live-search-feedback" aria-live="polite">
          <div v-if="hotelSearchState === 'ready'" class="live-feedback-card">
            <span class="state-icon" aria-hidden="true">⌖</span>
            <div>
              <h3>Ready to search</h3>
              <p>Enter a ZIP to find hotels from the live Geoapify Places response.</p>
            </div>
          </div>

          <div v-else-if="hotelSearchState === 'loading'" class="live-feedback-card" role="status">
            <span class="spinner" aria-hidden="true"></span>
            <div>
              <h3>Searching ZIP {{ requestedZip }}…</h3>
              <p>Confirming the postcode, then checking a 5 km radius.</p>
            </div>
          </div>

          <div
            v-else-if="hotelSearchState === 'invalid'"
            class="live-feedback-card live-feedback-error"
            role="alert"
          >
            <span class="state-icon" aria-hidden="true">!</span>
            <div>
              <h3>Invalid ZIP</h3>
              <p>{{ hotelSearchError }}</p>
            </div>
          </div>

          <div
            v-else-if="hotelSearchState === 'unresolved'"
            class="live-feedback-card live-feedback-error"
            role="alert"
          >
            <span class="state-icon" aria-hidden="true">?</span>
            <div>
              <h3>ZIP not resolved</h3>
              <p>{{ hotelSearchError }}</p>
            </div>
          </div>

          <div
            v-else-if="hotelSearchState === 'failed'"
            class="live-feedback-card live-feedback-error"
            role="alert"
          >
            <span class="state-icon" aria-hidden="true">!</span>
            <div>
              <h3>Live search unavailable</h3>
              <p>{{ hotelSearchError }}</p>
            </div>
          </div>

          <div v-else-if="hotelSearchState === 'empty'" class="live-feedback-card" role="status">
            <span class="state-icon" aria-hidden="true">⌕</span>
            <div>
              <h3>No nearby hotels</h3>
              <p>
                Geoapify resolved ZIP {{ hotelSearch.search_center.postcode }}, but returned no
                hotels within 5 km.
              </p>
            </div>
          </div>

          <div v-else-if="hotelSearchState === 'results'" class="live-feedback-card" role="status">
            <span class="state-icon" aria-hidden="true">✓</span>
            <div>
              <h3>
                {{ hotelSearch.count }}
                {{ hotelSearch.count === 1 ? 'hotel' : 'hotels' }} near ZIP
                {{ hotelSearch.search_center.postcode }}
              </h3>
              <p>
                Search centered on
                {{ displaySearchCenter(hotelSearch.search_center) }}.
              </p>
            </div>
          </div>
        </div>

        <div
          v-if="hotelSearch && (hotelSearchState === 'results' || hotelSearchState === 'empty')"
          class="live-results-layout"
        >
          <section class="live-hotel-list" aria-labelledby="live-list-title">
            <div class="live-panel-heading">
              <div>
                <p class="eyebrow">Provider results</p>
                <h3 id="live-list-title">Hotel list</h3>
              </div>
              <span>{{ hotelSearch.count }} within 5 km</span>
            </div>

            <ol v-if="liveHotels.length" class="live-hotel-results">
              <li v-for="(hotel, index) in liveHotels" :key="hotel.place_id">
                <button
                  :id="`live-hotel-${index}`"
                  :ref="(element) => setHotelListButton(hotel.place_id, element)"
                  type="button"
                  class="live-hotel-result"
                  :class="{ 'is-selected': selectedHotelId === hotel.place_id }"
                  :aria-pressed="selectedHotelId === hotel.place_id"
                  :aria-label="`Select ${hotel.name} on the map`"
                  @click="selectLiveHotel(hotel.place_id, 'list')"
                >
                  <span class="live-result-number" aria-hidden="true">{{ index + 1 }}</span>
                  <span class="live-result-copy">
                    <strong>{{ hotel.name }}</strong>
                    <span>{{ displayHotelLocation(hotel) }}</span>
                    <span
                      v-if="formatHotelDistance(hotel.distance_meters)"
                      class="live-result-meta"
                    >
                      {{ formatHotelDistance(hotel.distance_meters) }}
                    </span>
                    <span class="live-result-meta">
                      {{ hotel.latitude.toFixed(5) }}, {{ hotel.longitude.toFixed(5) }}
                    </span>
                  </span>
                  <span
                    v-if="selectedHotelId === hotel.place_id"
                    class="live-selected-label"
                  >
                    Selected
                  </span>
                </button>
              </li>
            </ol>

            <div v-else class="live-empty-list">
              <strong>No hotel records to list</strong>
              <span>The confirmed search center still appears on the map.</span>
            </div>
          </section>

          <section class="live-map-panel" aria-labelledby="live-map-title">
            <div class="live-panel-heading">
              <div>
                <p class="eyebrow">Same result set</p>
                <h3 id="live-map-title">Hotel map</h3>
              </div>
              <span>Search radius: 5 km</span>
            </div>
            <div
              ref="hotelMapElement"
              class="live-hotel-map"
              role="region"
              :aria-label="`Map of ${hotelSearch.count} hotels near ZIP ${hotelSearch.search_center.postcode}`"
            ></div>
          </section>
        </div>
      </section>

      <section class="traveler-bar" aria-labelledby="traveler-title">
        <div>
          <p class="eyebrow">Demo traveler</p>
          <h2 id="traveler-title">Who is booking?</h2>
          <p>Choose a traveler to book stays and view their saved booking history.</p>
        </div>
        <div class="traveler-select">
          <label for="traveler">Selected traveler</label>
          <select
            id="traveler"
            v-model="selectedUserId"
            :disabled="travelersLoading || Boolean(bookingAction)"
            @change="changeTraveler"
          >
            <option v-if="travelersLoading" value="">Loading travelers…</option>
            <option v-for="traveler in travelers" :key="traveler.user_id" :value="traveler.user_id">
              {{ traveler.display_name }} ({{ traveler.user_id }})
            </option>
          </select>
          <p v-if="travelersError" class="inline-error" role="alert">{{ travelersError }}</p>
        </div>
      </section>

      <section class="results" aria-label="Search results" aria-live="polite">
        <div v-if="loading" class="state-card">
          <span class="spinner" aria-hidden="true"></span>
          <p>Finding stays…</p>
        </div>

        <div v-else-if="error" class="state-card error-state" role="alert">
          <span class="state-icon" aria-hidden="true">!</span>
          <div>
            <h2>Search unavailable</h2>
            <p>{{ error }}</p>
          </div>
        </div>

        <div v-else-if="message" class="state-card">
          <span class="state-icon" aria-hidden="true">⌕</span>
          <div>
            <h2>No results to show</h2>
            <p>{{ message }}</p>
          </div>
        </div>

        <template v-else-if="stays.length">
          <div class="results-heading">
            <div>
              <p class="eyebrow">Available stays</p>
              <h2 id="results-title">{{ resultSummary }}</h2>
            </div>
            <p>Prices are estimated from nights × nightly rate.</p>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Trip</th>
                  <th scope="col">Hotel</th>
                  <th scope="col">Location</th>
                  <th scope="col">Check-in</th>
                  <th scope="col">Check-out</th>
                  <th scope="col">Nights</th>
                  <th scope="col">Nightly rate</th>
                  <th scope="col">Stay price</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="stay in stays" :key="stay.trip_id">
                  <td>
                    <strong>{{ stay.trip_name }}</strong>
                    <span class="secondary">{{ stay.trip_id }}</span>
                    <button
                      class="book-button"
                      type="button"
                      :disabled="!selectedUserId || Boolean(bookingAction)"
                      @click="createStayBooking(stay)"
                    >
                      {{ bookingAction === `create:${stay.trip_id}` ? 'Booking…' : 'Book this stay' }}
                    </button>
                  </td>
                  <td>{{ stay.hotel_name }}</td>
                  <td>{{ stay.city }}, {{ stay.state }}</td>
                  <td>{{ formatDate(stay.check_in) }}</td>
                  <td>{{ formatDate(stay.check_out) }}</td>
                  <td>{{ stay.nights }}</td>
                  <td>{{ formatCurrency(stay.nightly_rate_usd) }}</td>
                  <td class="price">{{ formatCurrency(stay.stay_price_usd) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <div v-else class="empty-prompt">
          <div class="empty-illustration" aria-hidden="true">⌂</div>
          <h2 id="results-title">Your hotel stays will appear here</h2>
          <p>Enter a hotel name or city above to search the sample data.</p>
        </div>
      </section>

      <section class="history" aria-labelledby="history-title">
        <div class="history-heading">
          <div>
            <p class="eyebrow">Saved trips</p>
            <h2 id="history-title">Booking history</h2>
            <p v-if="selectedTraveler">
              Showing bookings for {{ selectedTraveler.display_name }} ({{ selectedTraveler.user_id }}).
            </p>
          </div>
          <p id="booking-actions-help" class="action-explainer">
            <strong>Cancel</strong> keeps the booking in history. <strong>Delete</strong> permanently
            removes it.
          </p>
        </div>

        <p
          v-if="bookingFeedback"
          class="booking-feedback"
          :class="{ 'booking-feedback-error': bookingFeedbackType === 'error' }"
          :role="bookingFeedbackType === 'error' ? 'alert' : 'status'"
        >
          {{ bookingFeedback }}
        </p>

        <div v-if="historyLoading" class="history-state">
          <span class="spinner" aria-hidden="true"></span>
          <p>Loading booking history…</p>
        </div>

        <div v-else-if="historyError" class="history-state error-state" role="alert">
          <span class="state-icon" aria-hidden="true">!</span>
          <div>
            <h3>Booking history unavailable</h3>
            <p>{{ historyError }}</p>
          </div>
        </div>

        <div v-else-if="selectedTraveler && bookingHistory.length === 0" class="history-state">
          <span class="state-icon" aria-hidden="true">⌁</span>
          <div>
            <h3>No bookings yet</h3>
            <p>{{ selectedTraveler.display_name }} has no bookings. Search above to book a stay.</p>
          </div>
        </div>

        <div v-else-if="bookingHistory.length" class="table-wrap history-table-wrap">
          <table class="history-table">
            <thead>
              <tr>
                <th scope="col">Hotel</th>
                <th scope="col">Trip</th>
                <th scope="col">Check-in</th>
                <th scope="col">Check-out</th>
                <th scope="col">Booked on</th>
                <th scope="col">Status</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="booking in bookingHistory"
                :key="booking.booking_id"
                :class="{ 'cancelled-row': booking.status === 'cancelled' }"
              >
                <td>
                  <strong>{{ booking.stay.hotel_name }}</strong>
                  <span class="secondary">{{ booking.stay.city }}, {{ booking.stay.state }}</span>
                </td>
                <td>
                  <strong>{{ booking.stay.trip_name }}</strong>
                  <span class="secondary">{{ booking.booking_id }} · {{ booking.stay.trip_id }}</span>
                </td>
                <td>{{ formatDate(booking.stay.check_in) }}</td>
                <td>{{ formatDate(booking.stay.check_out) }}</td>
                <td>{{ formatDate(booking.booked_on) }}</td>
                <td>
                  <span class="status-badge" :class="`status-${booking.status}`">
                    {{ booking.status }}
                  </span>
                </td>
                <td class="booking-actions" aria-describedby="booking-actions-help">
                  <div class="primary-actions">
                    <button
                      class="cancel-button"
                      type="button"
                      :disabled="booking.status === 'cancelled' || Boolean(bookingAction)"
                      @click="cancelHistoryBooking(booking)"
                    >
                      {{
                        bookingAction === `cancel:${booking.booking_id}`
                          ? 'Cancelling…'
                          : booking.status === 'cancelled'
                            ? 'Cancelled'
                            : 'Cancel'
                      }}
                    </button>
                    <button
                      class="delete-button"
                      type="button"
                      :disabled="Boolean(bookingAction)"
                      :aria-expanded="deleteCandidateId === booking.booking_id"
                      @click="requestDelete(booking.booking_id)"
                    >
                      Delete
                    </button>
                  </div>

                  <div
                    v-if="deleteCandidateId === booking.booking_id"
                    class="delete-confirmation"
                    role="group"
                    :aria-label="`Confirm deletion of ${booking.booking_id}`"
                  >
                    <strong>Delete permanently?</strong>
                    <span>This removes {{ booking.booking_id }} entirely and cannot be undone.</span>
                    <div>
                      <button
                        class="confirm-delete-button"
                        type="button"
                        :disabled="Boolean(bookingAction)"
                        @click="deleteHistoryBooking(booking)"
                      >
                        {{
                          bookingAction === `delete:${booking.booking_id}`
                            ? 'Deleting…'
                            : 'Delete permanently'
                        }}
                      </button>
                      <button
                        class="keep-button"
                        type="button"
                        :disabled="Boolean(bookingAction)"
                        @click="deleteCandidateId = ''"
                      >
                        Keep booking
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <footer>
      <p>Expedia Lite · Fictional classroom travel data</p>
    </footer>
  </div>
</template>
