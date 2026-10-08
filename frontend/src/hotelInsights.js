export class HotelInsightRequestError extends Error {
  constructor(message, { status = 0 } = {}) {
    super(message)
    this.name = 'HotelInsightRequestError'
    this.status = status
  }
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function invalidResponse() {
  return new HotelInsightRequestError(
    'The saved hotel insights request returned an invalid response.',
  )
}

async function errorMessage(response, fallback) {
  try {
    const body = await response.json()
    return typeof body.detail === 'string' ? body.detail : fallback
  } catch {
    return fallback
  }
}

function validateTrace(trace, records, model) {
  if (
    !isObject(trace) ||
    trace.model !== model ||
    !['not_run', 'passed', 'rejected'].includes(trace.validation_status) ||
    typeof trace.query_executed !== 'boolean' ||
    typeof trace.second_request_sent !== 'boolean' ||
    !Array.isArray(trace.retrieved_records) ||
    JSON.stringify(trace.retrieved_records) !== JSON.stringify(records) ||
    (trace.proposed_sql !== null && typeof trace.proposed_sql !== 'string')
  ) {
    throw invalidResponse()
  }

  const isPassed =
    trace.validation_status === 'passed' &&
    typeof trace.proposed_sql === 'string' &&
    Boolean(trace.proposed_sql.trim()) &&
    trace.query_executed &&
    trace.second_request_sent
  const isRejected =
    trace.validation_status === 'rejected' &&
    typeof trace.proposed_sql === 'string' &&
    Boolean(trace.proposed_sql.trim()) &&
    !trace.query_executed &&
    !trace.second_request_sent &&
    records.length === 0
  const isNotRun =
    trace.validation_status === 'not_run' &&
    trace.proposed_sql === null &&
    !trace.query_executed &&
    !trace.second_request_sent &&
    records.length === 0
  if (!isPassed && !isRejected && !isNotRun) {
    throw invalidResponse()
  }
  return trace
}

function validateResult(payload, question) {
  if (
    !isObject(payload) ||
    payload.question !== question ||
    !['answer', 'no_matches', 'insufficient_data', 'rejected_query'].includes(payload.status) ||
    !Number.isInteger(payload.count) ||
    payload.count < 0 ||
    !Array.isArray(payload.records) ||
    payload.records.length !== payload.count ||
    payload.records.some((record) => !isObject(record)) ||
    typeof payload.model !== 'string' ||
    !payload.model
  ) {
    throw invalidResponse()
  }
  validateTrace(payload.trace, payload.records, payload.model)

  const statusAgreesWithTrace =
    (payload.status === 'answer' && payload.count > 0 && payload.trace.validation_status === 'passed') ||
    (payload.status === 'no_matches' && payload.count === 0 && payload.trace.validation_status === 'passed') ||
    (payload.status === 'rejected_query' && payload.count === 0 && payload.trace.validation_status === 'rejected') ||
    (payload.status === 'insufficient_data' &&
      (payload.trace.validation_status === 'not_run' || payload.trace.validation_status === 'passed'))
  if (!statusAgreesWithTrace) {
    throw invalidResponse()
  }

  if (payload.status === 'answer') {
    if (typeof payload.answer !== 'string' || !payload.answer.trim()) {
      throw invalidResponse()
    }
  } else if (typeof payload.message !== 'string' || !payload.message.trim()) {
    throw invalidResponse()
  }
  return payload
}

export async function askHotelInsights({ apiUrl, question, fetchImpl = fetch }) {
  let response
  try {
    response = await fetchImpl(`${apiUrl}/api/hotel-insights`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
      cache: 'no-store',
    })
  } catch {
    throw new HotelInsightRequestError(
      'The saved hotel insights request could not reach the backend.',
    )
  }

  if (!response.ok) {
    throw new HotelInsightRequestError(
      await errorMessage(response, 'The saved hotel insights request failed.'),
      { status: response.status },
    )
  }

  let payload
  try {
    payload = await response.json()
  } catch {
    throw invalidResponse()
  }
  return validateResult(payload, question)
}
