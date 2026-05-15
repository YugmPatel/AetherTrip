'use client'

import { useEffect, useState } from 'react'
import PlaceImagePlaceholder from '@/components/PlaceImagePlaceholder'
import SourceConfidence from '@/components/SourceConfidence'
import { EnrichedItineraryItem, TripResponse } from '@/lib/types'
import { cn, formatCurrency, getIssuesForItem, getUsableImageForItem } from '@/lib/utils'

type ItineraryStopCardProps = {
  item: EnrichedItineraryItem
  trip?: TripResponse | null
  selected?: boolean
  onSelect: (item: EnrichedItineraryItem) => void
}

function getBadges(item: EnrichedItineraryItem, trip?: TripResponse | null) {
  const issues = getIssuesForItem(trip, item)
  const badges = []
  const confidence = item.source_confidence || item.place?.confidence

  if (item.place?.verification_status === 'verified' || confidence && confidence >= 0.8) {
    badges.push({ label: 'Verified', className: 'border-emerald-300 bg-emerald-50 text-emerald-700' })
  }
  if (trip?.repair_history?.some((repair) => repair.attempted)) {
    badges.push({ label: 'Auto-Repaired', className: 'border-cyan-300 bg-cyan-50 text-[#0aaed3]' })
  }
  if (issues.some((issue) => ['warning', 'error', 'critical'].includes(issue.severity || 'warning'))) {
    badges.push({ label: 'Warning', className: 'border-amber-300 bg-amber-50 text-amber-700' })
  }
  if (typeof confidence === 'number' && confidence < 0.6) {
    badges.push({ label: 'Low Confidence', className: 'border-slate-300 bg-slate-50 text-slate-600' })
  }
  if (item.place?.dietary_tags?.some((tag) => tag.toLowerCase().includes('vegetarian'))) {
    badges.push({ label: 'Vegetarian-friendly', className: 'border-emerald-300 bg-emerald-50 text-emerald-700' })
  }
  if ((item.category || '').toLowerCase().includes('museum') || (item.category || '').toLowerCase().includes('indoor')) {
    badges.push({ label: 'Indoor Backup', className: 'border-slate-300 bg-slate-50 text-slate-600' })
  }

  return badges
}

export default function ItineraryStopCard({ item, trip, selected, onSelect }: ItineraryStopCardProps) {
  const badges = getBadges(item, trip)
  const issues = getIssuesForItem(trip, item)
  const currency = trip?.budget_report?.currency || 'USD'
  const usableImage = getUsableImageForItem(item)
  const [imageFailed, setImageFailed] = useState(false)

  useEffect(() => {
    setImageFailed(false)
  }, [usableImage?.url])

  return (
    <button
      type="button"
      onClick={() => onSelect(item)}
      className={cn(
        'w-full rounded-2xl border bg-white p-5 text-left shadow-[0_12px_30px_rgba(22,39,53,0.06)] transition hover:-translate-y-0.5 hover:shadow-[0_18px_40px_rgba(22,39,53,0.10)]',
        selected ? 'border-[#21c8ee] ring-4 ring-cyan-100' : 'border-[#edf2f6]'
      )}
    >
      <div className="flex gap-5">
        <div className="flex h-28 w-28 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-[#eaf3f8] text-xs font-black uppercase text-[#8a98aa]">
          {usableImage?.url && !imageFailed ? (
            <img
              src={usableImage.url}
              alt={item.place_name || 'Trip stop'}
              className="h-full w-full object-cover"
              onError={() => setImageFailed(true)}
            />
          ) : (
            <PlaceImagePlaceholder category={item.category || item.place?.category} />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-black text-[#607086]">
                {item.start_time || 'Time TBD'} {item.end_time ? `- ${item.end_time}` : ''}
              </p>
              <h3 className="mt-1 text-xl font-black tracking-[-0.03em] text-[#172033]">
                {item.place_name || 'Unnamed stop'}
              </h3>
              <p className="mt-1 text-sm font-semibold text-[#6a788b]">{item.address || item.place?.address || 'Address not verified'}</p>
            </div>
            <div className="flex flex-wrap justify-end gap-2">
              {badges.slice(0, 3).map((badge) => (
                <span key={badge.label} className={cn('rounded-full border px-2.5 py-1 text-[10px] font-black uppercase', badge.className)}>
                  {badge.label}
                </span>
              ))}
            </div>
          </div>

          <p className="line-clamp-2 text-sm font-medium leading-6 text-[#5f6e82]">
            {item.description || item.place?.description || 'No description returned by backend.'}
          </p>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            {item.category ? <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-bold text-[#607086]">{item.category}</span> : null}
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-bold text-[#607086]">
              {formatCurrency(item.estimated_cost || item.place?.estimated_cost || 0, currency)}
            </span>
            {typeof item.travel_time_from_previous_minutes === 'number' ? (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-bold text-[#607086]">
                {item.travel_time_from_previous_minutes} min from previous
              </span>
            ) : null}
            <SourceConfidence value={item.source_confidence || item.place?.confidence} />
          </div>

          {issues.length ? (
            <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs font-semibold leading-5 text-amber-800">
              {issues[0].message}
            </div>
          ) : null}
        </div>
      </div>
    </button>
  )
}
