'use client'

import { useEffect, useMemo, useRef } from 'react'
import maplibregl, { Map, Marker } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { EnrichedItineraryItem, TripResponse } from '@/lib/types'
import { getGeoapifyStyleUrl, getMapPoints } from '@/lib/map'

type TripMapProps = {
  trip?: TripResponse | null
  selectedDay?: number | 'all'
  selectedId?: string | null
  onSelect: (item: EnrichedItineraryItem) => void
}

export default function TripMap({ trip, selectedDay = 'all', selectedId, onSelect }: TripMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<Map | null>(null)
  const markersRef = useRef<Marker[]>([])
  const styleUrl = getGeoapifyStyleUrl()
  const points = useMemo(() => getMapPoints(trip, selectedDay), [trip, selectedDay])

  useEffect(() => {
    if (!containerRef.current || !styleUrl || !points.length) {
      return
    }

    if (!mapRef.current) {
      mapRef.current = new maplibregl.Map({
        container: containerRef.current,
        style: styleUrl,
        center: points[0].coordinates,
        zoom: 12,
        attributionControl: false,
      })
      mapRef.current.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right')
    }

    const map = mapRef.current
    markersRef.current.forEach((marker) => marker.remove())
    markersRef.current = []

    points.forEach((point) => {
      const markerEl = document.createElement('button')
      markerEl.type = 'button'
      markerEl.className = `flex h-8 w-8 items-center justify-center rounded-full border-2 border-white text-xs font-black text-white shadow-lg ${
        selectedId === point.id ? 'bg-[#0f172a]' : 'bg-[#21c8ee]'
      }`
      markerEl.textContent = point.label
      markerEl.onclick = () => onSelect(point.stop)
      const marker = new maplibregl.Marker({ element: markerEl }).setLngLat(point.coordinates).addTo(map)
      markersRef.current.push(marker)
    })

    const route = {
      type: 'Feature' as const,
      geometry: {
        type: 'LineString' as const,
        coordinates: points.map((point) => point.coordinates),
      },
      properties: {},
    }

    const updateRoute = () => {
      if (!map.getSource('trip-route')) {
        map.addSource('trip-route', { type: 'geojson', data: route })
        map.addLayer({
          id: 'trip-route',
          type: 'line',
          source: 'trip-route',
          paint: {
            'line-color': '#21c8ee',
            'line-width': 3,
            'line-dasharray': [2, 2],
          },
        })
      } else {
        const source = map.getSource('trip-route') as maplibregl.GeoJSONSource
        source.setData(route)
      }
    }

    if (map.isStyleLoaded()) {
      updateRoute()
    } else {
      map.once('load', updateRoute)
    }

    const bounds = new maplibregl.LngLatBounds()
    points.forEach((point) => bounds.extend(point.coordinates))
    if (points.length > 1) {
      map.fitBounds(bounds, { padding: 70, maxZoom: 13 })
    } else {
      map.setCenter(points[0].coordinates)
    }
  }, [onSelect, points, selectedId, styleUrl])

  if (!styleUrl) {
    return (
      <section className="rounded-2xl border border-[#edf2f6] bg-white p-6 shadow-[0_20px_60px_rgba(22,39,53,0.08)]">
        <h2 className="text-lg font-black tracking-[-0.03em]">Verified Route</h2>
        <div className="mt-4 flex h-64 items-center justify-center rounded-xl bg-[#e9eff6] px-6 text-center text-sm font-bold text-[#657184]">
          Map unavailable because NEXT_PUBLIC_GEOAPIFY_API_KEY is not configured.
        </div>
      </section>
    )
  }

  if (!points.length) {
    return (
      <section className="rounded-2xl border border-[#edf2f6] bg-white p-6 shadow-[0_20px_60px_rgba(22,39,53,0.08)]">
        <h2 className="text-lg font-black tracking-[-0.03em]">Verified Route</h2>
        <div className="mt-4 flex h-64 items-center justify-center rounded-xl bg-[#e9eff6] px-6 text-center text-sm font-bold text-[#657184]">
          Map unavailable because itinerary coordinates were not returned.
        </div>
      </section>
    )
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-[#edf2f6] bg-white shadow-[0_20px_60px_rgba(22,39,53,0.08)]">
      <div className="flex items-center justify-between border-b border-[#edf2f6] px-6 py-4">
        <h2 className="text-lg font-black tracking-[-0.03em]">Verified Route</h2>
        <span className="rounded-full border border-[#d7e2ec] px-3 py-1 text-xs font-black text-[#657184]">Interactive</span>
      </div>
      <div ref={containerRef} className="h-72 w-full bg-[#e9eff6]" />
    </section>
  )
}
