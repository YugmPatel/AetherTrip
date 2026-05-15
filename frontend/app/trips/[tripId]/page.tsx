'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import BudgetBreakdownCard from '@/components/BudgetBreakdownCard'
import DataSourcesCard from '@/components/DataSourcesCard'
import FeasibilityScoreCard from '@/components/FeasibilityScoreCard'
import Footer from '@/components/Footer'
import Header from '@/components/Header'
import ItineraryTimeline from '@/components/ItineraryTimeline'
import PlaceDetailDrawer from '@/components/PlaceDetailDrawer'
import RepairHistory from '@/components/RepairHistory'
import TripMap from '@/components/TripMap'
import ValidationWarnings from '@/components/ValidationWarnings'
import WhyThisTripWorks from '@/components/WhyThisTripWorks'
import { getTrip } from '@/lib/api'
import { getTripFromSupabase } from '@/lib/trip-storage'
import { EnrichedItineraryItem, TripResponse } from '@/lib/types'
import { getDestination, getTripMeta, getTripTitle, readStoredTrip, readTripNotice, storeTrip, TripNotice } from '@/lib/utils'

export default function TripResultPage() {
  const params = useParams<{ tripId: string }>()
  const tripId = params.tripId
  const [trip, setTrip] = useState<TripResponse | null>(null)
  const [selectedStop, setSelectedStop] = useState<EnrichedItineraryItem | null>(null)
  const [selectedDay, setSelectedDay] = useState<number | 'all'>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState<TripNotice | null>(null)

  useEffect(() => {
    let active = true

    async function loadTrip() {
      setLoading(true)
      setError('')
      setNotice(readTripNotice(tripId))
      const stored = readStoredTrip(tripId)
      if (stored) {
        setTrip(stored)
        setLoading(false)
        return
      }

      const supabaseTrip = await getTripFromSupabase(tripId)
      if (!active) {
        return
      }

      if (supabaseTrip.found) {
        setTrip(supabaseTrip.trip)
        storeTrip(supabaseTrip.trip)
        setLoading(false)
        return
      }

      try {
        const response = await getTrip(tripId)
        if (!active) {
          return
        }
        setTrip(response)
        storeTrip(response)
      } catch (requestError) {
        if (active) {
          setError(requestError instanceof Error ? requestError.message : 'Trip not found.')
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadTrip()
    return () => {
      active = false
    }
  }, [tripId])

  useEffect(() => {
    if (!notice) {
      return
    }

    const timeout = window.setTimeout(() => setNotice(null), 6000)
    return () => window.clearTimeout(timeout)
  }, [notice])

  const days = trip?.itinerary?.days || []
  function handleSelectStop(stop: EnrichedItineraryItem) {
    setSelectedStop(stop)
    if (stop.day) {
      setSelectedDay(stop.day)
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-[#f7fafc] text-[#172033]">
        <Header />
        <div className="flex min-h-[70vh] items-center justify-center text-sm font-black text-[#657184]">Loading trip...</div>
      </main>
    )
  }

  if (error || !trip) {
    return (
      <main className="min-h-screen bg-[#f7fafc] text-[#172033]">
        <Header />
        <div className="mx-auto max-w-2xl px-6 py-20">
          <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-red-700">
            <h1 className="text-2xl font-black">Unable to load itinerary</h1>
            <p className="mt-3 text-sm font-semibold">{error || 'Trip not found.'}</p>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-[#f7fafc] text-[#172033]">
      <Header />
      {notice ? (
        <div
          className={`fixed right-5 top-24 z-50 rounded-xl border px-5 py-3 text-sm font-black shadow-[0_18px_45px_rgba(22,39,53,0.14)] ${
            notice.type === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
              : notice.type === 'warning'
                ? 'border-amber-200 bg-amber-50 text-amber-800'
                : 'border-cyan-200 bg-cyan-50 text-[#087f99]'
          }`}
        >
          {notice.message}
        </div>
      ) : null}
      <section className="mx-auto max-w-[1180px] px-5 py-10 sm:px-8">
        <div className="flex flex-col justify-between gap-6 border-b border-[#dce5ea] pb-8 lg:flex-row lg:items-end">
          <div>
            <h1 className="text-[40px] font-black leading-tight tracking-[-0.055em] md:text-[50px]">
              {getTripTitle(trip)}
            </h1>
            <p className="mt-3 text-lg font-semibold text-[#657184]">{getTripMeta(trip)}</p>
            <p className="mt-2 text-sm font-semibold text-[#8a98aa]">Destination: {getDestination(trip)}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => window.print()}
              className="h-11 rounded-lg border border-[#cbd7e2] bg-white px-5 text-sm font-black text-[#172033] transition hover:bg-slate-50"
            >
              Export PDF
            </button>
            <button
              type="button"
              disabled
              title="Recalculation endpoint not available yet."
              className="h-11 rounded-lg bg-[#21c8ee] px-5 text-sm font-black text-white opacity-60"
            >
              Recalculate
            </button>
          </div>
        </div>

        <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_430px]">
          <div>
            <ItineraryTimeline trip={trip} selectedId={selectedStop?.stableId} onSelect={handleSelectStop} />

            <section className="mt-10 rounded-2xl border border-dashed border-[#d6e2eb] bg-white p-10 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#eaf3f8] text-2xl font-black text-[#7c8ea4]">
                +
              </div>
              <h2 className="mt-5 text-2xl font-black tracking-[-0.04em]">Add to your journey</h2>
              <p className="mx-auto mt-3 max-w-md text-sm font-medium leading-6 text-[#657184]">
                Need more activities for the evening? AetherTrip can verify extra events once recommendation endpoints are available.
              </p>
              <button
                type="button"
                disabled
                title="Recommendation endpoint not available yet."
                className="mt-6 h-11 rounded-lg border border-[#cbd7e2] bg-white px-5 text-sm font-black text-[#657184]"
              >
                Browse Recommendations
              </button>
            </section>
          </div>

          <aside className="space-y-6 lg:sticky lg:top-24 lg:self-start">
            <FeasibilityScoreCard score={trip.feasibility_score} />

            {days.length > 1 ? (
              <div className="flex flex-wrap gap-2 rounded-2xl border border-[#edf2f6] bg-white p-3 shadow-[0_20px_60px_rgba(22,39,53,0.08)]">
                <button
                  type="button"
                  onClick={() => setSelectedDay('all')}
                  className={`rounded-full px-3 py-1.5 text-xs font-black ${selectedDay === 'all' ? 'bg-[#21c8ee] text-white' : 'bg-slate-100 text-[#657184]'}`}
                >
                  All
                </button>
                {days.map((day) => (
                  <button
                    type="button"
                    key={day.day}
                    onClick={() => setSelectedDay(day.day || 'all')}
                    className={`rounded-full px-3 py-1.5 text-xs font-black ${selectedDay === day.day ? 'bg-[#21c8ee] text-white' : 'bg-slate-100 text-[#657184]'}`}
                  >
                    Day {day.day}
                  </button>
                ))}
              </div>
            ) : null}

            <TripMap trip={trip} selectedDay={selectedDay} selectedId={selectedStop?.stableId} onSelect={handleSelectStop} />
            <DataSourcesCard trip={trip} />
            <BudgetBreakdownCard budget={trip.budget_report} />
            <ValidationWarnings trip={trip} />
            <RepairHistory repairs={trip.repair_history} />
            <WhyThisTripWorks trip={trip} />
          </aside>
        </div>
      </section>

      <PlaceDetailDrawer item={selectedStop} trip={trip} onClose={() => setSelectedStop(null)} />
      <Footer />
    </main>
  )
}
