'use client'

import ItineraryStopCard from '@/components/ItineraryStopCard'
import { EnrichedItineraryItem, TripResponse } from '@/lib/types'
import { enrichItem, getDayLabel } from '@/lib/utils'

type ItineraryTimelineProps = {
  trip?: TripResponse | null
  selectedId?: string | null
  onSelect: (item: EnrichedItineraryItem) => void
}

export default function ItineraryTimeline({ trip, selectedId, onSelect }: ItineraryTimelineProps) {
  const days = trip?.itinerary?.days || []
  const places = trip?.place_candidates || []

  if (!days.length) {
    return (
      <section className="rounded-2xl border border-dashed border-[#d6e2eb] bg-white p-10 text-center">
        <h2 className="text-xl font-black">No itinerary days returned</h2>
        <p className="mt-2 text-sm font-medium text-[#6a788b]">
          The backend response did not include day-by-day itinerary items.
        </p>
      </section>
    )
  }

  return (
    <section className="space-y-10">
      {days.map((day) => (
        <div key={`${day.day}-${day.date || ''}`} className="relative pl-8">
          <span className="absolute left-0 top-1 flex h-7 w-7 items-center justify-center rounded-full bg-[#172033] text-xs font-black text-white">
            {day.day || ''}
          </span>
          <h2 className="text-3xl font-black tracking-[-0.04em] text-[#172033]">{getDayLabel(day)}</h2>
          {day.weather_summary ? <p className="mt-2 text-sm font-semibold text-[#6a788b]">{day.weather_summary}</p> : null}

          <div className="mt-6 space-y-5 border-l border-[#dce7ef] pl-6">
            {(day.items || []).map((item, index) => {
              const enriched = enrichItem(item, index, places)
              return (
                <div key={enriched.stableId} className="relative">
                  <span className="absolute -left-[31px] top-10 h-3 w-3 rounded-full border-2 border-white bg-[#21c8ee] shadow-[0_0_0_4px_rgba(33,200,238,0.16)]" />
                  <ItineraryStopCard
                    item={enriched}
                    trip={trip}
                    selected={selectedId === enriched.stableId}
                    onSelect={onSelect}
                  />
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </section>
  )
}
