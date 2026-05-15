import { PipelineEvent, TripResponse } from '@/lib/types'
import { cleanDisplayMessage, normalizeTripResponse } from '@/lib/utils'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

async function parseApiError(response: Response) {
  try {
    const body = await response.json()
    return cleanDisplayMessage(body?.detail || body?.message || response.statusText)
  } catch {
    return cleanDisplayMessage(response.statusText)
  }
}

export async function planTrip(userInput: string): Promise<TripResponse> {
  const response = await fetch(`${API_BASE_URL}/api/trips/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput }),
  })

  if (!response.ok) {
    throw new Error(await parseApiError(response))
  }

  return normalizeTripResponse(await response.json()) as TripResponse
}

export async function streamPlanTrip(
  userInput: string,
  onEvent: (event: PipelineEvent) => void
): Promise<TripResponse> {
  const response = await fetch(`${API_BASE_URL}/api/trips/plan/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ user_input: userInput }),
  })

  if (!response.ok || !response.body) {
    onEvent({
      stage: 'planning_request',
      label: 'Planning Request',
      status: 'running',
      message: 'Streaming unavailable. Waiting for the backend planning request to finish.',
      agent: 'AetherTrip API',
      service: 'FastAPI',
      progress_percent: 0,
    })
    const trip = await planTrip(userInput)
    onEvent({
      stage: 'completed',
      label: 'Completed',
      status: 'completed',
      message: 'Trip plan is ready.',
      agent: 'AetherTrip API',
      service: 'FastAPI',
      progress_percent: 100,
      trip,
    })
    return trip
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let finalTrip: TripResponse | null = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''

    for (const rawEvent of events) {
      const dataLine = rawEvent
        .split('\n')
        .find((line) => line.startsWith('data:'))
        ?.replace(/^data:\s*/, '')

      if (!dataLine) {
        continue
      }

      const event = JSON.parse(dataLine) as PipelineEvent
      onEvent(event)

      if (event.status === 'failed') {
        throw new Error(event.message || 'Trip planning failed.')
      }

      if (event.trip) {
        finalTrip = normalizeTripResponse(event.trip)
      }
    }
  }

  if (!finalTrip) {
    throw new Error('Planning stream ended before returning a trip.')
  }

  return finalTrip
}

export async function getTrip(tripId: string): Promise<TripResponse> {
  const response = await fetch(`${API_BASE_URL}/api/trips/${tripId}`)
  if (!response.ok) {
    throw new Error(await parseApiError(response))
  }

  return normalizeTripResponse(await response.json()) as TripResponse
}

export async function repairTrip(tripId: string): Promise<TripResponse> {
  const response = await fetch(`${API_BASE_URL}/api/trips/${tripId}/repair`, {
    method: 'POST',
  })

  if (response.status === 404 || response.status === 405) {
    throw new Error('Recalculation endpoint not available yet.')
  }

  if (!response.ok) {
    throw new Error(await parseApiError(response))
  }

  return normalizeTripResponse(await response.json()) as TripResponse
}
