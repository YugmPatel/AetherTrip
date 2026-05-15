import assert from 'node:assert/strict'
import { test } from 'node:test'
import { getMapPoints } from '@/lib/map'
import {
  UNKNOWN_VERIFY_TEXT,
  buildWhyTripSections,
  formatRepairHistoryItem,
  getCanonicalBudgetStatus,
  getPlaceDetailValidation,
  getWhyTripTitle,
} from '@/lib/resultPage'
import { enrichItem, formatCurrency, getDestination } from '@/lib/utils'
import { EnrichedItineraryItem, TripResponse } from '@/lib/types'

const validTrip: TripResponse = {
  constraints: { hard: { destination: 'Los Angeles', duration_days: 3, travelers: 4 } },
  itinerary: {
    destination: 'Los Angeles',
    days: [{
      day: 1,
      items: [{
        day: 1,
        place_id: 'p1',
        place_name: 'Grand Central Market',
        category: 'restaurant',
        start_time: '12:00',
        end_time: '13:00',
        description: 'Lunch',
        estimated_cost: 25,
        latitude: 34.0505,
        longitude: -118.2487,
      }],
    }],
  },
  budget_report: { status: 'unknown', is_over_budget: false },
  place_candidates: [],
}

test('map extraction returns coordinates from itinerary items', () => {
  const points = getMapPoints(validTrip, 'all')

  assert.equal(points.length, 1)
  assert.deepEqual(points[0].coordinates, [-118.2487, 34.0505])
})

test('budget formatting handles missing values', () => {
  assert.equal(formatCurrency(undefined), 'Unknown')
})

test('itinerary card mapping displays backend place_name', () => {
  const item = validTrip.itinerary?.days?.[0]?.items?.[0]
  assert.equal(item ? enrichItem(item, 0, []).place_name : '', 'Grand Central Market')
})

test('itinerary image mapping preserves item image_url', () => {
  const item = validTrip.itinerary?.days?.[0]?.items?.[0]
  const enriched = item ? enrichItem({ ...item, image_url: 'https://upload.wikimedia.org/example.jpg' }, 0, []) : null

  assert.equal(enriched?.image_url, 'https://upload.wikimedia.org/example.jpg')
})

test('itinerary image mapping falls back to candidate image_url', () => {
  const item = validTrip.itinerary?.days?.[0]?.items?.[0]
  const enriched = item
    ? enrichItem({ ...item, image_url: null }, 0, [{
        id: 'p1',
        name: 'Grand Central Market',
        category: 'restaurant',
        latitude: 34.0505,
        longitude: -118.2487,
        image_url: 'https://upload.wikimedia.org/candidate.jpg',
        image_source: 'wikimedia',
        image_confidence: 0.9,
      }])
    : null

  assert.equal(enriched?.image_url, 'https://upload.wikimedia.org/candidate.jpg')
  assert.equal(enriched?.image_source, 'wikimedia')
  assert.equal(enriched?.image_confidence, 0.9)
})

test('no static Tokyo or Unknown data appears when backend returns valid trip', () => {
  const display = `${getDestination(validTrip)} ${validTrip.itinerary?.days?.[0]?.items?.[0]?.place_name}`

  assert.match(display, /Los Angeles/)
  assert.doesNotMatch(display, /Tokyo|Unknown/)
})

test('test_budget_over_limit_not_within_budget', () => {
  const status = getCanonicalBudgetStatus({
    per_person_cost: 1119,
    budget_limit: 500,
    is_over_budget: false,
    status: 'within_budget',
  })

  assert.equal(status.status, 'over_budget')
  assert.equal(status.isOverBudget, true)
  assert.equal(status.label, 'Over budget')
})

test('test_place_detail_drawer_shows_opening_hours_unknown', () => {
  const item: EnrichedItineraryItem = {
    stableId: 'p2',
    day: 1,
    start_time: '10:00',
    end_time: '11:00',
    place_id: 'p2',
    place_name: 'Unknown Hours Cafe',
    category: 'restaurant',
    description: 'Coffee',
    place: {
      id: 'p2',
      name: 'Unknown Hours Cafe',
      category: 'restaurant',
      latitude: 34,
      longitude: -118,
      opening_hours: null,
      sources: [],
    },
  }

  assert.equal(getPlaceDetailValidation(item, validTrip).openingHoursStatus, UNKNOWN_VERIFY_TEXT)
})

test('test_place_detail_drawer_shows_weather_risk_unknown', () => {
  const baseItem = validTrip.itinerary?.days?.[0]?.items?.[0]
  assert.ok(baseItem)
  const item = enrichItem(baseItem, 0, [])

  assert.equal(getPlaceDetailValidation(item, validTrip).weatherRisk, UNKNOWN_VERIFY_TEXT)
})

test('test_why_this_trip_works_no_raw_markdown', () => {
  const trip: TripResponse = {
    ...validTrip,
    feasibility_score: { overall_score: 65, grade: 'D' },
    why_this_trip_works: '## Feasibility\n**Needs review**\n\n- Route Status: `tight`\n\n[Notes](https://example.com): verify hours',
  }
  const normalizedSections = buildWhyTripSections(trip)
  const renderedText = normalizedSections.flatMap((section) => [section.title, ...section.items]).join('\n')
  const copiedText = normalizedSections.flatMap((section) => [section.title, ...section.items]).join('\n')

  assert.equal(getWhyTripTitle(trip), 'Why This Trip Needs Review')
  assert.equal(copiedText, renderedText)
  assert.doesNotMatch(renderedText, /[#*`]/)
  assert.doesNotMatch(renderedText, /\[[^\]]+\]\([^)]+\)/)
})

test('test_repair_history_no_object_object', () => {
  const formatted = formatRepairHistoryItem({
    type: 'route_time_remove_stop',
    changed: true,
    why: 'Schedule remained impossible.',
    before: { place_ids: ['p1', 'p2'] },
    after: { place_ids: ['p1'] },
  })
  const renderedText = Object.values(formatted).join(' ')

  assert.equal(formatted.action, 'Route Time Remove Stop')
  assert.match(renderedText, /Place Ids: p1, p2/)
  assert.doesNotMatch(renderedText, /\[object Object\]/)
})
