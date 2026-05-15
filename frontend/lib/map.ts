import { EnrichedItineraryItem, TripResponse } from '@/lib/types'
import { getAllStops } from '@/lib/utils'

export type MapPoint = {
  id: string
  label: string
  coordinates: [number, number]
  stop: EnrichedItineraryItem
}

export function getMapPoints(trip?: TripResponse | null, selectedDay?: number | 'all'): MapPoint[] {
  return getAllStops(trip)
    .filter((stop) => selectedDay === 'all' || !selectedDay || stop.day === selectedDay)
    .filter((stop) => typeof stop.latitude === 'number' && typeof stop.longitude === 'number')
    .map((stop, index) => ({
      id: stop.stableId,
      label: String(index + 1),
      coordinates: [stop.longitude as number, stop.latitude as number],
      stop,
    }))
}

export function getGeoapifyStyleUrl() {
  const provider = process.env.NEXT_PUBLIC_MAP_PROVIDER || 'geoapify'
  const renderer = process.env.NEXT_PUBLIC_MAP_RENDERER || 'maplibre'
  const apiKey = process.env.NEXT_PUBLIC_GEOAPIFY_API_KEY
  if (provider !== 'geoapify' || renderer !== 'maplibre' || !apiKey) {
    return null
  }

  return `https://maps.geoapify.com/v1/styles/osm-bright/style.json?apiKey=${apiKey}`
}
