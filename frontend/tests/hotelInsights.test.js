import assert from 'node:assert/strict'
import test from 'node:test'

import { askHotelInsights } from '../src/hotelInsights.js'

const apiUrl = 'http://backend.test'
const question = 'Which saved hotel can provide two rooms?'
const model = 'nvidia/class-nemotron:free'
const sql = 'SELECT provider_place_id, hotel_name FROM saved_hotels LIMIT 50'
const records = [
  {
    provider_place_id: 'provider-1',
    hotel_name: 'Saved Hotel',
    total_cost_cents: 67000,
  },
]

function trace(overrides = {}) {
  return {
    model,
    proposed_sql: sql,
    validation_status: 'passed',
    query_executed: true,
    retrieved_records: records,
    second_request_sent: true,
    ...overrides,
  }
}

function response(body, { ok = true, status = 200 } = {}) {
  return {
    ok,
    status,
    async json() {
      return body
    },
  }
}

test('answer accepts the exact two-request SQL trace and retrieved records', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push([url, options])
    return response({
      status: 'answer',
      question,
      count: 1,
      records,
      answer: 'Saved Hotel has a $670.00 simulated classroom total.',
      model,
      trace: trace(),
    })
  }

  const result = await askHotelInsights({ apiUrl, question, fetchImpl })

  assert.equal(result.status, 'answer')
  assert.deepEqual(result.records, records)
  assert.equal(result.trace.second_request_sent, true)
  assert.equal(calls[0][0], `${apiUrl}/api/hotel-insights`)
  assert.deepEqual(JSON.parse(calls[0][1].body), { question })
  assert.equal(calls[0][1].cache, 'no-store')
})

test('no matches, insufficient data, and rejected query stay distinct', async (t) => {
  const cases = [
    {
      status: 'no_matches',
      count: 0,
      records: [],
      message: 'No saved hotels match the requested conditions.',
      trace: trace({ retrieved_records: [] }),
    },
    {
      status: 'insufficient_data',
      count: 0,
      records: [],
      message: 'The requested stay is outside stored coverage.',
      trace: trace({
        proposed_sql: null,
        validation_status: 'not_run',
        query_executed: false,
        retrieved_records: [],
        second_request_sent: false,
      }),
    },
    {
      status: 'rejected_query',
      count: 0,
      records: [],
      message: 'Generated query was rejected.',
      trace: trace({
        validation_status: 'rejected',
        query_executed: false,
        retrieved_records: [],
        second_request_sent: false,
      }),
    },
  ]

  for (const item of cases) {
    await t.test(item.status, async () => {
      const result = await askHotelInsights({
        apiUrl,
        question,
        fetchImpl: async () => response({ question, model, ...item }),
      })
      assert.equal(result.status, item.status)
    })
  }
})

test('HTTP, network, and malformed responses are honest failures', async (t) => {
  await t.test('HTTP', async () => {
    await assert.rejects(
      askHotelInsights({
        apiUrl,
        question,
        fetchImpl: async () =>
          response(
            { detail: 'OpenRouter answer generation failed.' },
            { ok: false, status: 502 },
          ),
      }),
      (error) => error.status === 502 && error.message.includes('answer generation'),
    )
  })

  await t.test('network', async () => {
    await assert.rejects(
      askHotelInsights({
        apiUrl,
        question,
        fetchImpl: async () => {
          throw new Error('offline')
        },
      }),
      /could not reach the backend/,
    )
  })

  await t.test('malformed', async () => {
    await assert.rejects(
      askHotelInsights({
        apiUrl,
        question,
        fetchImpl: async () =>
          response({
            status: 'answer',
            question,
            count: 1,
            records,
            answer: 'Missing trace.',
            model,
          }),
      }),
      /invalid response/,
    )
  })

  await t.test('trace records must exactly match response records', async () => {
    await assert.rejects(
      askHotelInsights({
        apiUrl,
        question,
        fetchImpl: async () =>
          response({
            status: 'answer',
            question,
            count: 1,
            records,
            answer: 'Mismatch.',
            model,
            trace: trace({ retrieved_records: [] }),
          }),
      }),
      /invalid response/,
    )
  })

  await t.test('answer and no-match statuses must agree with record count', async () => {
    for (const item of [
      {
        status: 'answer',
        count: 0,
        records: [],
        answer: 'Invented answer.',
        trace: trace({ retrieved_records: [] }),
      },
      {
        status: 'no_matches',
        count: 1,
        records,
        message: 'No saved hotels match.',
        trace: trace(),
      },
    ]) {
      await assert.rejects(
        askHotelInsights({
          apiUrl,
          question,
          fetchImpl: async () => response({ question, model, ...item }),
        }),
        /invalid response/,
      )
    }
  })

  await t.test('trace flags must describe one valid pipeline state', async () => {
    await assert.rejects(
      askHotelInsights({
        apiUrl,
        question,
        fetchImpl: async () =>
          response({
            status: 'answer',
            question,
            count: 1,
            records,
            answer: 'Saved Hotel matches.',
            model,
            trace: trace({ second_request_sent: false }),
          }),
      }),
      /invalid response/,
    )
  })
})
