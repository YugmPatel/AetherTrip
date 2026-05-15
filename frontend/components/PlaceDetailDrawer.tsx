'use client'

import { useEffect, useState } from 'react'
import PlaceImagePlaceholder from '@/components/PlaceImagePlaceholder'
import SourceConfidence from '@/components/SourceConfidence'
import { EnrichedItineraryItem, TripResponse } from '@/lib/types'
import { getPlaceDetailValidation } from '@/lib/resultPage'
import { formatCurrency, getImageConfidenceValue, getIssuesForItem, getUsableImageForItem } from '@/lib/utils'

type PlaceDetailDrawerProps = {
  item: EnrichedItineraryItem | null
  trip?: TripResponse | null
  onClose: () => void
}

export default function PlaceDetailDrawer({ item, trip, onClose }: PlaceDetailDrawerProps) {
  const [imageFailed, setImageFailed] = useState(false)
  const imageResetKey = [
    item?.image_url,
    item?.place?.image_url,
    item?.place?.place_image_url,
  ]
    .filter(Boolean)
    .join('|')

  useEffect(() => {
    setImageFailed(false)
  }, [imageResetKey])

  if (!item) {
    return null
  }

  const place = item.place
  const issues = [...(item.validation_issues || []), ...(place?.validation_issues || []), ...getIssuesForItem(trip, item)]
  const currency = trip?.budget_report?.currency || 'USD'
  const validation = getPlaceDetailValidation(item, trip)
  const usableImage = getUsableImageForItem(item)
  const imageSource = item.image_source || place?.image_source || null
  const imageCredit = item.image_credit || place?.image_credit || null
  const imageConfidence = getImageConfidenceValue(item.image_confidence ?? place?.image_confidence ?? null)

  return (
    <div className="fixed inset-0 z-50 bg-[#0b1320]/35 backdrop-blur-sm" onClick={onClose}>
      <aside
        className="absolute right-0 top-0 h-full w-full max-w-[460px] overflow-y-auto bg-white p-7 shadow-[-24px_0_80px_rgba(11,19,32,0.22)]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-6">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.12em] text-[#21c8ee]">{item.category || 'Place'}</p>
            <h2 className="mt-2 text-3xl font-black tracking-[-0.04em] text-[#172033]">{item.place_name || place?.name || 'Unnamed stop'}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-[#d7e2ec] text-xl font-bold text-[#657184] hover:bg-slate-50"
            aria-label="Close detail drawer"
          >
            x
          </button>
        </div>

        <div className="mt-7 space-y-6">
          <section>
            <div className="h-56 overflow-hidden rounded-2xl bg-[#eaf3f8]">
              {usableImage?.url && !imageFailed ? (
                <img
                  src={usableImage.url}
                  alt={item.place_name || place?.name || 'Trip stop'}
                  className="h-full w-full object-cover"
                  onError={() => setImageFailed(true)}
                />
              ) : (
                <PlaceImagePlaceholder category={item.category || place?.category} />
              )}
            </div>
            {usableImage?.url && !imageFailed ? (
              <div className="mt-2 space-y-1 text-xs font-semibold text-[#657184]">
                {imageSource ? <p>Image source: {imageSource}</p> : null}
                {imageCredit ? <p>Credit: {imageCredit}</p> : null}
                {typeof imageConfidence === 'number' ? <p>Image confidence: {Math.round(imageConfidence * 100)}%</p> : null}
              </div>
            ) : null}
          </section>

          <section>
            <h3 className="text-sm font-black text-[#172033]">Description</h3>
            <p className="mt-2 text-sm font-medium leading-6 text-[#657184]">
              {item.description || place?.description || 'No description returned.'}
            </p>
          </section>

          <section className="grid gap-3 rounded-2xl bg-[#f7fafc] p-4 text-sm font-semibold text-[#657184]">
            <p><span className="font-black text-[#172033]">Address:</span> {item.address || place?.address || 'Unknown'}</p>
            <p>
              <span className="font-black text-[#172033]">Coordinates:</span>{' '}
              {typeof item.latitude === 'number' && typeof item.longitude === 'number'
                ? `${item.latitude.toFixed(5)}, ${item.longitude.toFixed(5)}`
                : 'Not verified'}
            </p>
            <p><span className="font-black text-[#172033]">Estimated cost:</span> {formatCurrency(item.estimated_cost || place?.estimated_cost || 0, currency)}</p>
            <p><span className="font-black text-[#172033]">Scheduled window:</span> {validation.scheduledTimeWindow}</p>
            <p><span className="font-black text-[#172033]">Validation status:</span> {validation.validationStatus}</p>
          </section>

          <section className="rounded-2xl border border-[#dce5ea] bg-white p-4">
            <h3 className="text-sm font-black text-[#172033]">Opening Hours</h3>
            <p className="mt-2 rounded-xl bg-[#f7fafc] p-3 text-sm font-black text-[#405268]">
              {validation.scheduledOpenStatus}
            </p>
            <p className="mt-2 text-sm font-semibold leading-6 text-[#657184]">
              Status: {validation.openingHoursStatus}
            </p>
            <pre className="mt-2 whitespace-pre-wrap rounded-xl bg-[#f7fafc] p-4 text-xs font-semibold leading-5 text-[#657184]">
              {validation.openingHoursText}
            </pre>
          </section>

          <section className="rounded-2xl border border-[#dce5ea] bg-white p-4">
            <h3 className="text-sm font-black text-[#172033]">Weather Risk</h3>
            <div className="mt-3 grid gap-2 text-sm font-semibold text-[#657184]">
              <p><span className="font-black text-[#172033]">Risk:</span> {validation.weatherRiskLevel}</p>
              <p><span className="font-black text-[#172033]">Outdoor activity:</span> {validation.isOutdoor === null ? 'Unknown' : validation.isOutdoor ? 'Yes' : 'No'}</p>
              <p><span className="font-black text-[#172033]">Reason:</span> {validation.weatherRiskReason || validation.weatherRisk}</p>
            </div>
          </section>

          <section>
            <h3 className="text-sm font-black text-[#172033]">Source Confidence</h3>
            <div className="mt-3">
              <SourceConfidence value={item.source_confidence || place?.confidence} />
            </div>
            <div className="mt-4 space-y-2">
              {(place?.sources || []).length ? (
                place?.sources?.map((source, index) => (
                  <p key={`${source.name}-${index}`} className="text-sm font-semibold text-[#657184]">
                    {source.name || 'Unknown source'} {typeof source.confidence === 'number' ? `(${Math.round(source.confidence * 100)}%)` : ''}
                  </p>
                ))
              ) : (
                <p className="text-sm font-semibold text-[#657184]">Provider info not returned.</p>
              )}
            </div>
          </section>

          <section>
            <h3 className="text-sm font-black text-[#172033]">Validation Status</h3>
            {issues.length ? (
              <div className="mt-3 space-y-2">
                {issues.map((issue, index) => (
                  <div key={index} className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm font-semibold leading-5 text-amber-800">
                    {issue.message || issue.evidence || 'Validation issue returned without message.'}
                    {issue.suggested_fix ? <p className="mt-1 text-xs opacity-80">Suggested fix: {issue.suggested_fix}</p> : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-3 rounded-xl bg-emerald-50 p-3 text-sm font-bold text-emerald-700">
                No item-specific issues returned.
              </p>
            )}
          </section>

          <section>
            <h3 className="text-sm font-black text-[#172033]">Why It Was Selected</h3>
            <p className="mt-2 text-sm font-medium leading-6 text-[#657184]">
              {item.notes || 'The backend did not return a specific selection rationale for this stop.'}
            </p>
          </section>
        </div>
      </aside>
    </div>
  )
}
