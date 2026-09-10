<script setup>
import { computed, ref } from 'vue'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const city = ref('')
const searchedCity = ref('')
const stays = ref([])
const loading = ref(false)
const message = ref('')
const error = ref('')

const resultSummary = computed(() => {
  if (!searchedCity.value || loading.value || error.value || message.value) {
    return ''
  }

  const count = stays.value.length
  return `${count} ${count === 1 ? 'stay' : 'stays'} in ${searchedCity.value}`
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

async function search() {
  const query = city.value.trim()
  stays.value = []
  searchedCity.value = ''
  message.value = ''
  error.value = ''

  if (!query) {
    message.value = 'Enter a city to search for available stays.'
    return
  }

  loading.value = true
  try {
    const response = await fetch(`${API_URL}/api/stays?city=${encodeURIComponent(query)}`)
    if (!response.ok) {
      throw new Error('The search service returned an error.')
    }

    const data = await response.json()
    stays.value = data.stays
    searchedCity.value = data.query

    if (data.count === 0) {
      message.value = `No hotel stays found for ${data.query}. Try another city.`
    }
  } catch {
    error.value = 'We could not complete the search. Confirm the backend is running and try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <a class="brand" href="#" aria-label="Expedia Lite home">
        <span class="brand-mark" aria-hidden="true">↗</span>
        <span>Expedia Lite</span>
      </a>
      <span class="course-label">CSV hotel search</span>
    </header>

    <main>
      <section class="hero" aria-labelledby="page-title">
        <p class="eyebrow">Find your next stay</p>
        <h1 id="page-title">Where are you going?</h1>
        <p class="intro">
          Search our sample hotel stays by city. Dates and prices come directly from the
          supplied travel data.
        </p>

        <form class="search-card" @submit.prevent="search">
          <label for="city">City</label>
          <div class="search-row">
            <div class="input-wrap">
              <span aria-hidden="true">⌖</span>
              <input
                id="city"
                v-model="city"
                name="city"
                type="text"
                autocomplete="off"
                placeholder="Try Boston or New York"
              />
            </div>
            <button type="submit" :disabled="loading">
              {{ loading ? 'Searching…' : 'Search' }}
            </button>
          </div>
          <p class="city-hints">Also available: Philadelphia, Washington, and State College</p>
        </form>
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
          <p>Enter a full city name above to search the sample data.</p>
        </div>
      </section>
    </main>

    <footer>
      <p>Expedia Lite · Fictional classroom travel data</p>
    </footer>
  </div>
</template>
