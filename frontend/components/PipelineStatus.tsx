'use client'

import { PipelineEvent, PipelineStatus as Status } from '@/lib/types'
import { cn } from '@/lib/utils'

type PipelineStatusProps = {
  events: PipelineEvent[]
}

const categories = ['Source Integrity', 'Constraint Match', 'Budget Stability', 'Safety Check']

export const defaultPipelineStages = [
  { stage: 'understanding_request', label: 'Understanding Request' },
  { stage: 'extracting_constraints', label: 'Extracting Constraints' },
  { stage: 'geocoding_destination', label: 'Geocoding Destination' },
  { stage: 'fetching_places_geoapify', label: 'Fetching Real Places' },
  { stage: 'fetching_weather_open_meteo', label: 'Checking Weather' },
  { stage: 'building_route_matrix_openrouteservice', label: 'Calculating Travel Times' },
  { stage: 'building_candidate_itinerary', label: 'Building Candidate Itinerary' },
  { stage: 'validating_opening_hours', label: 'Validating Opening Hours' },
  { stage: 'validating_travel_time', label: 'Validating Travel Time' },
  { stage: 'validating_budget', label: 'Validating Budget' },
  { stage: 'validating_weather', label: 'Validating Weather' },
  { stage: 'auto_repair_if_needed', label: 'Repairing If Needed' },
  { stage: 'scoring_feasibility', label: 'Scoring Feasibility' },
  { stage: 'explanation_agent', label: 'Generating Explanation' },
  { stage: 'completed', label: 'Completed' },
]

export function getLatestEvents(events: PipelineEvent[]) {
  const latest = new Map<string, PipelineEvent>()
  events.forEach((event) => latest.set(event.stage, event))
  return latest
}

export function getCurrentEvent(events: PipelineEvent[]) {
  return [...events].reverse().find((event) => event.status === 'running') || [...events].reverse()[0]
}

export function getStageStatus(stage: string, latest: Map<string, PipelineEvent>): Status {
  return latest.get(stage)?.status || 'pending'
}

export default function PipelineStatus({ events }: PipelineStatusProps) {
  const latestEvent = events[events.length - 1]
  const percent = Math.max(0, Math.min(100, latestEvent?.progress_percent || 0))

  return (
    <section className="mx-auto max-w-[760px] rounded-2xl border border-[#edf2f6] bg-white p-6 shadow-[0_16px_45px_rgba(22,39,53,0.06)]">
      <div className="flex items-center justify-between gap-5">
        <h2 className="text-sm font-black text-[#344256]">Feasibility Confidence Forecast</h2>
        <span className="text-sm font-black text-[#21c8ee]">{percent}% Verified</span>
      </div>
      <div className="mt-5 h-3 overflow-hidden rounded-full bg-[#edf3f7]">
        <div className="h-full rounded-full bg-[#21c8ee] transition-[width] duration-300" style={{ width: `${percent}%` }} />
      </div>
      <div className="mt-7 grid grid-cols-2 gap-4 md:grid-cols-4">
        {categories.map((category, index) => {
          const filled = percent >= (index + 1) * 22
          const partial = percent >= index * 22
          return (
            <div key={category}>
              <div
                className={cn(
                  'h-1.5 rounded-full',
                  filled ? 'bg-emerald-500' : partial ? 'bg-amber-400' : 'bg-[#dfe7ef]'
                )}
              />
              <p className="mt-3 text-center text-[10px] font-black uppercase tracking-[0.08em] text-[#8a98aa]">
                {category}
              </p>
            </div>
          )
        })}
      </div>
    </section>
  )
}
