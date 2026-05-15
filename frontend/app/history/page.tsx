'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import Header from '@/components/Header'
import { getLoginPath, useAuthSession } from '@/lib/auth'
import { deleteTripFromSupabase, getSupabaseHistoryErrorMessage, listTripsFromSupabase, SavedTripRow } from '@/lib/trip-storage'
import { formatCurrency } from '@/lib/utils'

function formatDate(value?: string | null) {
  if (!value) {
    return 'Unknown date'
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))
}

function scoreLabel(trip: SavedTripRow) {
  if (typeof trip.feasibility_score !== 'number') {
    return 'Score pending'
  }

  return `${trip.feasibility_score}%${trip.feasibility_status ? ` | ${trip.feasibility_status}` : ''}`
}

export default function HistoryPage() {
  const { user, hydrated } = useAuthSession()
  const [trips, setTrips] = useState<SavedTripRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function loadTrips() {
      if (!hydrated) {
        return
      }

      if (!user) {
        setLoading(false)
        return
      }

      setLoading(true)
      setError('')
      const result = await listTripsFromSupabase()
      if (!active) {
        return
      }

      setTrips(result.trips)
      setError(result.reason ? getSupabaseHistoryErrorMessage(result.error, result.reason) : '')
      setLoading(false)
    }

    void loadTrips()

    return () => {
      active = false
    }
  }, [hydrated, user])

  async function handleDelete(tripId: string) {
    const result = await deleteTripFromSupabase(tripId)
    if (result.deleted) {
      setTrips((current) => current.filter((trip) => trip.trip_id !== tripId))
    } else if (result.reason) {
      setError(getSupabaseHistoryErrorMessage('error' in result ? result.error : undefined, result.reason))
    }
  }

  if (!hydrated || loading) {
    return (
      <main className="min-h-screen bg-[#f7fafc] text-[#172033]">
        <Header />
        <div className="flex min-h-[70vh] items-center justify-center text-sm font-black text-[#657184]">
          Loading history...
        </div>
      </main>
    )
  }

  if (!user) {
    return (
      <main className="min-h-screen bg-[#f7fafc] text-[#172033]">
        <Header />
        <section className="mx-auto max-w-2xl px-6 py-20 text-center">
          <div className="rounded-2xl border border-[#dce5ea] bg-white p-10 shadow-[0_18px_45px_rgba(22,39,53,0.05)]">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[#21c8ee]">Saved trips</p>
            <h1 className="mt-3 text-3xl font-black tracking-[-0.04em]">Sign in to view your saved trips.</h1>
            <p className="mx-auto mt-3 max-w-md text-sm font-medium leading-6 text-[#65707b]">
              Generated trips still work while logged out, but persistent history needs your AetherTrip account.
            </p>
            <Link
              href={getLoginPath('/history')}
              className="mt-7 inline-flex h-12 items-center justify-center rounded-lg bg-[#21c8ee] px-7 text-sm font-black text-white shadow-[0_14px_28px_rgba(33,200,238,0.25)] transition hover:-translate-y-0.5 hover:bg-[#15bde5]"
            >
              Login
            </Link>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-[#f7fafc] text-[#172033]">
      <Header />
      <section className="mx-auto max-w-[1180px] px-5 py-10 sm:px-8">
        <div className="flex flex-col justify-between gap-5 border-b border-[#dce5ea] pb-8 md:flex-row md:items-end">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[#21c8ee]">History</p>
            <h1 className="mt-3 text-[40px] font-black leading-tight tracking-[-0.055em] md:text-[50px]">
              Saved itineraries
            </h1>
            <p className="mt-3 text-lg font-semibold text-[#657184]">
              Reopen trips saved to Supabase without regenerating them.
            </p>
          </div>
          <Link
            href="/plan"
            className="inline-flex h-12 items-center justify-center rounded-lg bg-[#21c8ee] px-6 text-sm font-black text-white shadow-[0_14px_28px_rgba(33,200,238,0.25)] transition hover:-translate-y-0.5 hover:bg-[#15bde5]"
          >
            New Plan
          </Link>
        </div>

        {error ? (
          <div className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 p-8 text-amber-900">
            <h2 className="text-xl font-black tracking-[-0.03em]">History setup needs attention</h2>
            <p className="mt-3 text-sm font-bold leading-6">{error}</p>
            <p className="mt-3 text-sm font-medium leading-6">
              Run `supabase/schema.sql` in the Supabase SQL Editor, then run `notify pgrst, 'reload schema';`.
            </p>
          </div>
        ) : trips.length ? (
          <div className="mt-8 grid gap-5">
            {trips.map((trip) => (
              <article
                key={trip.trip_id}
                className="rounded-2xl border border-[#dce5ea] bg-white p-6 shadow-[0_18px_45px_rgba(22,39,53,0.05)]"
              >
                <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-center">
                  <div>
                    <h2 className="text-2xl font-black tracking-[-0.035em]">{trip.title || 'Saved itinerary'}</h2>
                    <p className="mt-2 text-sm font-semibold text-[#657184]">
                      {trip.destination || 'Destination not specified'} | {formatDate(trip.created_at)}
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2 text-xs font-black text-[#405268]">
                      <span className="rounded-full bg-[#eafbff] px-3 py-1.5">
                        {trip.duration_days ? `${trip.duration_days} days` : 'Flexible dates'}
                      </span>
                      <span className="rounded-full bg-[#f1f5f9] px-3 py-1.5">
                        {trip.travelers ? `${trip.travelers} traveler${trip.travelers === 1 ? '' : 's'}` : 'Travelers open'}
                      </span>
                      <span className="rounded-full bg-[#f1f5f9] px-3 py-1.5">
                        {trip.budget_per_person ? `${formatCurrency(trip.budget_per_person)}/person` : 'Budget open'}
                      </span>
                      <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-emerald-700">{scoreLabel(trip)}</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <Link
                      href={`/trips/${trip.trip_id}`}
                      className="inline-flex h-11 items-center justify-center rounded-lg bg-[#21c8ee] px-5 text-sm font-black text-white transition hover:-translate-y-0.5 hover:bg-[#15bde5]"
                    >
                      Open itinerary
                    </Link>
                    <button
                      type="button"
                      onClick={() => void handleDelete(trip.trip_id)}
                      className="h-11 rounded-lg border border-[#d4dde5] bg-white px-5 text-sm font-black text-[#657184] transition hover:border-red-200 hover:bg-red-50 hover:text-red-600"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="mt-10 rounded-2xl border border-dashed border-[#cfdbe2] bg-white p-12 text-center">
            <h2 className="text-2xl font-black tracking-[-0.04em]">No saved trips yet</h2>
            <p className="mx-auto mt-3 max-w-md text-sm font-medium leading-6 text-[#65707b]">
              Generate a trip while signed in and AetherTrip will save it here automatically.
            </p>
            <Link
              href="/plan"
              className="mt-7 inline-flex h-12 items-center justify-center rounded-lg bg-[#21c8ee] px-7 text-sm font-black text-white"
            >
              Plan a trip
            </Link>
          </div>
        )}
      </section>
    </main>
  )
}
