<script setup>
import { computed, onMounted, ref } from 'vue'

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

const selectedTraveler = computed(() =>
  travelers.value.find((traveler) => traveler.user_id === selectedUserId.value),
)

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
