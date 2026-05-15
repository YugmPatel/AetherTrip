import { DayPlan, EnrichedItineraryItem, ItineraryItem, PlaceCandidate, TripResponse, ValidationIssue } from '@/lib/types'

export function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ')
}

export function formatCurrency(value?: number | null, currency = 'USD') {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'Unknown'
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: value % 1 === 0 ? 0 : 2,
  }).format(value)
}

export function formatPercent(value?: number | null) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'Unknown'
  }

  return `${Math.round(value)}%`
}

export function confidencePercent(value?: number | null) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return undefined
  }

  return value <= 1 ? Math.round(value * 100) : Math.round(value)
}

function hasMeaningfulText(value?: string | null) {
  if (!value) {
    return false
  }

  const normalized = value.trim().toLowerCase()
  return Boolean(normalized) && !['unknown', 'your trip', 'trip destination'].includes(normalized)
}

export function getDestination(trip?: TripResponse | null) {
  const constraintDestination = trip?.constraints?.hard?.destination || trip?.constraints?.destination
  const itineraryDestination = trip?.itinerary?.destination

  if (hasMeaningfulText(constraintDestination)) {
    return constraintDestination as string
  }

  if (hasMeaningfulText(itineraryDestination)) {
    return itineraryDestination as string
  }

  return 'Your Trip'
}

export function getTripTitle(trip?: TripResponse | null) {
  const destination = getDestination(trip)
  return destination === 'Your Trip' ? 'Your Verified Itinerary' : `Your ${destination} Itinerary`
}

export function getTripMeta(trip?: TripResponse | null) {
  const hard = trip?.constraints?.hard
  const days = hard?.duration_days ?? trip?.constraints?.duration_days ?? trip?.itinerary?.days?.length
  const travelers = hard?.travelers ?? trip?.constraints?.travelers ?? trip?.budget_report?.travelers
  const budgetLimit = hard?.budget_per_person ?? trip?.constraints?.budget_per_person ?? trip?.budget_report?.budget_limit ?? trip?.budget_report?.user_budget_per_person
  const pieces = [
    hard?.start_date && hard?.end_date ? `${hard.start_date} - ${hard.end_date}` : null,
    days ? `${days} Days` : null,
    travelers ? `${travelers} Traveler${travelers === 1 ? '' : 's'}` : null,
    typeof budgetLimit === 'number' ? `${formatCurrency(budgetLimit, hard?.currency || trip?.budget_report?.currency || 'USD')}/person` : null,
  ].filter(Boolean)

  return pieces.length ? pieces.join(' | ') : 'Dates, travelers, and budget were not fully specified.'
}

export function buildPlaceLookup(places?: PlaceCandidate[]) {
  return new Map((places || []).filter((place) => place.id).map((place) => [place.id as string, place]))
}

export function enrichItem(item: ItineraryItem, index: number, places?: PlaceCandidate[]): EnrichedItineraryItem {
  const lookup = buildPlaceLookup(places)
  const embeddedPlace = item.place || null
  const place = item.place_id ? lookup.get(item.place_id) || embeddedPlace : embeddedPlace
  return {
    ...item,
    stableId: item.place_id || `${item.day || 'day'}-${index}-${item.place_name || place?.name || 'stop'}`,
    place_name: item.place_name || place?.name,
    category: item.category || place?.category,
    estimated_cost: item.estimated_cost ?? place?.estimated_cost ?? undefined,
    address: item.address || place?.address || null,
    latitude: item.latitude ?? item.place?.latitude ?? place?.latitude,
    longitude: item.longitude ?? item.place?.longitude ?? place?.longitude,
    source_confidence: item.source_confidence ?? place?.source_confidence ?? place?.confidence,
    verification_status: item.verification_status || place?.verification_status || null,
    opening_hours_status: item.opening_hours_status || place?.opening_hours_status || null,
    opening_hours_text: item.opening_hours_text || place?.opening_hours_text || null,
    scheduled_open_status: item.scheduled_open_status || place?.scheduled_open_status || null,
    scheduled_time_window: item.scheduled_time_window || place?.scheduled_time_window || null,
    weather_risk: item.weather_risk || place?.weather_risk || null,
    weather_risk_level: item.weather_risk_level || place?.weather_risk_level || null,
    weather_risk_reason: item.weather_risk_reason || place?.weather_risk_reason || null,
    is_outdoor: item.is_outdoor ?? place?.is_outdoor ?? null,
    validation_status: item.validation_status || place?.validation_status || null,
    validation_issues: item.validation_issues || place?.validation_issues || [],
    image_url: item.image_url || place?.image_url || place?.place_image_url || null,
    image_source: item.image_source || place?.image_source || null,
    image_credit: item.image_credit || place?.image_credit || null,
    image_confidence: item.image_confidence ?? place?.image_confidence ?? null,
    place,
  }
}

export function getAllStops(trip?: TripResponse | null) {
  const normalized = normalizeTripResponse(trip)
  const places = normalized?.place_candidates || []
  return (normalized?.itinerary?.days || []).flatMap((day) =>
    (day.items || []).map((item, index) => enrichItem(item, index, places))
  )
}

export function normalizeTripResponse(trip?: TripResponse | null): TripResponse | null {
  if (!trip) {
    return null
  }

  const raw = trip as TripResponse & Record<string, unknown>
  const constraints = raw.constraints || null
  const hard = constraints?.hard || constraints || {}
  const rawItinerary = raw.itinerary || (raw as { itinerary?: TripResponse['itinerary']; days?: unknown }).itinerary || {}
  const itineraryRecord = rawItinerary as NonNullable<TripResponse['itinerary']> & Record<string, unknown>
  const rawDays = (Array.isArray(itineraryRecord.days) ? itineraryRecord.days : Array.isArray(raw.days) ? raw.days : []) as DayPlan[]
  const places = raw.place_candidates || []

  const normalizedDays = rawDays.map((day, dayIndex) => {
    const dayNumber = day.day ?? day.day_number ?? dayIndex + 1
    return {
      ...day,
      day: dayNumber,
      day_number: day.day_number ?? dayNumber,
      title: day.title || `Day ${dayNumber}`,
      items: (day.items || []).map((item, itemIndex) => enrichItem({ ...item, day: item.day ?? dayNumber }, itemIndex, places)),
    }
  })

  return {
    ...raw,
    constraints: constraints
      ? {
          ...constraints,
          hard: constraints.hard || {
            origin: hard.origin,
            destination: hard.destination,
            duration_days: hard.duration_days,
            travelers: hard.travelers,
            budget_per_person: hard.budget_per_person,
            diet: hard.diet,
            transport_mode: hard.transport_mode,
          },
        }
      : constraints,
    itinerary: {
      ...itineraryRecord,
      destination: itineraryRecord.destination || hard.destination,
      days: normalizedDays,
    },
    budget_report: raw.budget_report || null,
    service_status: raw.service_status || raw.data_sources,
    data_sources: raw.data_sources || raw.service_status,
  }
}

export function cleanDisplayMessage(message?: string | null) {
  if (!message) {
    return ''
  }

  return message.replace(/https:\/\/errors\.pydantic\.dev\/\S+/g, '').trim()
}

export function getIssues(trip?: TripResponse | null) {
  const reports = trip?.validation_reports || []
  const reportIssues = reports.flatMap((report) => [...(report.issues || []), ...(report.warnings || [])])
  const warningIssues: ValidationIssue[] = (trip?.warnings || []).map((message) => ({
    severity: 'warning',
    message: cleanDisplayMessage(message),
    type: 'trip_warning',
  }))
  return [...reportIssues, ...warningIssues]
    .map((issue) => ({ ...issue, message: cleanDisplayMessage(issue.message) }))
    .filter((issue) => issue.message)
}

export function getIssuesForItem(trip: TripResponse | null | undefined, item: ItineraryItem) {
  const itemName = (item.place_name || item.place?.name || '').trim().toLowerCase()

  return getIssues(trip).filter((issue) => {
    if (issue.place_id && item.place_id && issue.place_id === item.place_id) {
      return true
    }

    if (issue.place_name && itemName && issue.place_name.trim().toLowerCase() === itemName) {
      return true
    }

    const issueText = [issue.message, issue.evidence, issue.suggested_fix].filter(Boolean).join(' ').toLowerCase()
    if (itemName && issueText.includes(itemName)) {
      return true
    }

    if (issue.day && item.day && issue.day === item.day && !issue.place_id && !issue.place_name && !itemName) {
      return true
    }

    return false
  })
}

export function getImageConfidenceValue(value?: number | null) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null
  }

  return value > 1 ? value / 100 : value
}

function imageSourceText(item: ItineraryItem) {
  return [
    item.image_source,
    item.place?.image_source,
    item.place?.source,
    item.place?.source_provider,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

function hasVerifiedImageSignal(item: ItineraryItem) {
  const status = [
    item.validation_status,
    item.verification_status,
    item.place?.validation_status,
    item.place?.verification_status,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
  const confidence = getImageConfidenceValue(item.source_confidence ?? item.place?.source_confidence ?? item.place?.confidence)

  return status.includes('verified') || status.includes('high') || (typeof confidence === 'number' && confidence >= 0.8)
}

export function getUsableImageForItem(item: ItineraryItem) {
  const url = item.image_url || item.place?.image_url || item.place?.place_image_url || null
  if (!url) {
    return null
  }

  const confidence = getImageConfidenceValue(item.image_confidence ?? item.place?.image_confidence ?? null)
  if (typeof confidence === 'number') {
    return confidence >= 0.65 ? { url, confidence } : null
  }

  const source = imageSourceText(item)
  const isWikiSource = source.includes('wikimedia') || source.includes('wikipedia')
  if (isWikiSource && hasVerifiedImageSignal(item)) {
    return { url, confidence: null }
  }

  return null
}

export function getDayLabel(day: DayPlan) {
  return `Day ${day.day || ''}${day.date ? ` | ${day.date}` : ''}`
}

export function normalizeBreakdownKey(key: string) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .replace('Travel Time', 'Travel Time / Route')
}

export function storeTrip(trip: TripResponse) {
  const normalized = normalizeTripResponse(trip)
  if (typeof window === 'undefined' || !normalized?.trip_id) {
    return
  }

  window.sessionStorage.setItem(`aethertrip.trip.${normalized.trip_id}`, JSON.stringify(normalized))
}

export type TripNotice = {
  type: 'success' | 'info' | 'warning'
  message: string
}

export function storeTripNotice(tripId: string | undefined, notice: TripNotice) {
  if (typeof window === 'undefined' || !tripId) {
    return
  }

  window.sessionStorage.setItem(`aethertrip.notice.${tripId}`, JSON.stringify(notice))
}

export function readTripNotice(tripId: string) {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const key = `aethertrip.notice.${tripId}`
    const value = window.sessionStorage.getItem(key)
    if (!value) {
      return null
    }

    window.sessionStorage.removeItem(key)
    return JSON.parse(value) as TripNotice
  } catch {
    return null
  }
}

export function readStoredTrip(tripId: string) {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const value = window.sessionStorage.getItem(`aethertrip.trip.${tripId}`)
    return value ? normalizeTripResponse(JSON.parse(value) as TripResponse) : null
  } catch {
    return null
  }
}
