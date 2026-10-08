import assert from 'node:assert/strict'
import test from 'node:test'

import {
  DEMO_NIGHT_DATES,
  formatStoredRate,
  removeHotelLocally,
  saveHotelLocally,
  searchHotelsLocalFirst,
} from '../src/hotelStorage.js'

const apiUrl = 'http://backend.test'

function response(body, { ok = true, status = 200 } = {}) {
  return {
    ok,
    status,
    async json() {
      return body
    },
  }
}

function savedHotel(overrides = {}) {
  return {
    place_id: 'provider-1',
    name: 'Saved Hotel',
    address: '1 Local Way',
    latitude: 42.36,
    longitude: -71.06,
    searched_zips: ['02108'],
    nights: DEMO_NIGHT_DATES.map((date, index) => ({
      date,
      nightly_rate_cents: index === 1 ? 0 : 10000,
      rooms_available: index === 1 ? 0 : 20,
    })),
    ...overrides,
  }
}

function apiPayload() {
  return {
    search_center: { postcode: '02108', latitude: 42.36, longitude: -71.06 },
    radius_meters: 5000,
    count: 1,
    hotels: [
      {
        place_id: 'provider-2',
        name: 'API Hotel',
        latitude: 42.37,
        longitude: -71.05,
      },
    ],
  }
}

test('a local hit is labeled and never calls the Part 1 hotel endpoint', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push([url, options])
    return response({ zip: '02108', count: 1, hotels: [savedHotel()] })
  }

  const result = await searchHotelsLocalFirst({ apiUrl, postcode: '02108', fetchImpl })

  assert.equal(result.source, 'local')
  assert.equal(result.label, 'Saved locally')
  assert.deepEqual(calls, [
    [`${apiUrl}/api/saved-hotels?zip=02108`, { cache: 'no-store' }],
  ])
})

test('a successful empty local lookup falls back to the Part 1 endpoint in order', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push([url, options])
    if (url.includes('/api/saved-hotels?')) {
      return response({ zip: '02108', count: 0, hotels: [] })
    }
    return response(apiPayload())
  }

  const result = await searchHotelsLocalFirst({ apiUrl, postcode: '02108', fetchImpl })

  assert.equal(result.source, 'api')
  assert.equal(result.label, 'API results')
  assert.deepEqual(
    calls.map(([url]) => url),
    [`${apiUrl}/api/saved-hotels?zip=02108`, `${apiUrl}/api/hotels?zip=02108`],
  )
})

test('local HTTP, network, and malformed-response failures never fall back', async (t) => {
  const cases = [
    async () => response({ detail: 'Saved hotel lookup failed.' }, { ok: false, status: 500 }),
    async () => {
      throw new Error('offline')
    },
    async () => response({ zip: '02108', count: 0 }),
  ]

  for (const [index, implementation] of cases.entries()) {
    await t.test(`failure ${index + 1}`, async () => {
      const calls = []
      const fetchImpl = async (url) => {
        calls.push(url)
        return implementation()
      }
      await assert.rejects(
        searchHotelsLocalFirst({ apiUrl, postcode: '02108', fetchImpl }),
        (error) => error.phase === 'local',
      )
      assert.deepEqual(calls, [`${apiUrl}/api/saved-hotels?zip=02108`])
    })
  }
})

test('each explicit search rereads saved values without cache', async () => {
  let rate = 10000
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push([url, options])
    return response({
      zip: '02108',
      count: 1,
      hotels: [
        savedHotel({
          nights: DEMO_NIGHT_DATES.map((date, index) => ({
            date,
            nightly_rate_cents: index === 0 ? rate : 10000,
            rooms_available: index === 0 ? 0 : 20,
          })),
        }),
      ],
    })
  }

  const first = await searchHotelsLocalFirst({ apiUrl, postcode: '02108', fetchImpl })
  rate = 12345
  const second = await searchHotelsLocalFirst({ apiUrl, postcode: '02108', fetchImpl })

  assert.equal(first.payload.hotels[0].nights[0].nightly_rate_cents, 10000)
  assert.equal(second.payload.hotels[0].nights[0].nightly_rate_cents, 12345)
  assert.ok(calls.every(([, options]) => options.cache === 'no-store'))
})

test('save and remove use the implemented mutation contracts', async () => {
  const hotel = apiPayload().hotels[0]
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push([url, options])
    if (options.method === 'POST') {
      return response(savedHotel({ place_id: hotel.place_id, name: hotel.name }))
    }
    return response({ place_id: hotel.place_id, deleted: true })
  }

  await saveHotelLocally({ apiUrl, postcode: '02108', hotel, fetchImpl })
  await removeHotelLocally({ apiUrl, placeId: hotel.place_id, fetchImpl })

  assert.equal(calls[0][0], `${apiUrl}/api/saved-hotels`)
  assert.deepEqual(JSON.parse(calls[0][1].body), { searched_zip: '02108', hotel })
  assert.equal(calls[1][0], `${apiUrl}/api/saved-hotels/provider-2`)
  assert.equal(calls[1][1].method, 'DELETE')
})

test('failed save and remove requests stay distinct from successful mutations', async () => {
  const hotel = apiPayload().hotels[0]
  const failedSave = async () =>
    response({ detail: 'Saved hotel save failed.' }, { ok: false, status: 500 })
  const failedRemove = async () =>
    response({ detail: 'Saved hotel removal failed.' }, { ok: false, status: 500 })

  await assert.rejects(
    saveHotelLocally({ apiUrl, postcode: '02108', hotel, fetchImpl: failedSave }),
    (error) =>
      error.phase === 'save' &&
      error.status === 500 &&
      error.message === 'Saved hotel save failed.',
  )
  await assert.rejects(
    removeHotelLocally({ apiUrl, placeId: hotel.place_id, fetchImpl: failedRemove }),
    (error) =>
      error.phase === 'remove' &&
      error.status === 500 &&
      error.message === 'Saved hotel removal failed.',
  )
})

test('stored cents and zero values are formatted without defaults', () => {
  assert.equal(formatStoredRate(10000), '$100.00')
  assert.equal(formatStoredRate(0), '$0.00')
  assert.equal(savedHotel().nights[1].rooms_available, 0)
})

test('saved records require exactly the five fixed classroom nights', async () => {
  const fetchImpl = async () =>
    response({
      zip: '02108',
      count: 1,
      hotels: [savedHotel({ nights: savedHotel().nights.slice(0, 4) })],
    })

  await assert.rejects(
    searchHotelsLocalFirst({ apiUrl, postcode: '02108', fetchImpl }),
    (error) => error.phase === 'local' && error.message.includes('invalid response'),
  )
})
