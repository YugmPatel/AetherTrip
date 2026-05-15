'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import ProductHeader from '@/components/ProductHeader'
import UserAvatar from '@/components/UserAvatar'
import { getLoginPath, signOutAuth, useAuthSession } from '@/lib/auth'
import { countTripsFromSupabase, getSupabaseHistoryErrorMessage, listTripsFromSupabase, SavedTripRow } from '@/lib/trip-storage'
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

export default function ProfilePage() {
  const router = useRouter()
  const { user, hydrated } = useAuthSession()
  const [trips, setTrips] = useState<SavedTripRow[]>([])
  const [tripCount, setTripCount] = useState<number | null>(null)
  const [tripsError, setTripsError] = useState('')
  const [loadingTrips, setLoadingTrips] = useState(true)

  useEffect(() => {
    if (hydrated && !user) {
      router.replace(getLoginPath('/profile'))
    }
  }, [hydrated, router, user])

  useEffect(() => {
    let active = true

    async function loadTrips() {
      if (!user) {
        setLoadingTrips(false)
        return
      }

      setLoadingTrips(true)
      setTripsError('')
      const [countResult, recentResult] = await Promise.all([
        countTripsFromSupabase(),
        listTripsFromSupabase(3),
      ])
      if (active) {
        setTripCount(countResult.count)
        setTrips(recentResult.trips)
        const failed = countResult.reason ? countResult : recentResult.reason ? recentResult : null
        setTripsError(failed?.reason ? getSupabaseHistoryErrorMessage(failed.error, failed.reason) : '')
        setLoadingTrips(false)
      }
    }

    void loadTrips()

    return () => {
      active = false
    }
  }, [user])

  async function handleSignOut() {
    await signOutAuth()
    router.replace('/')
    router.refresh()
  }

  if (!hydrated || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white text-sm font-bold text-slate-600">
        Checking profile...
      </div>
    )
  }

  const recentTrips = trips

  return (
    <main className="min-h-screen bg-[#f7fafc] text-[#171b22]">
      <ProductHeader />

      <section className="mx-auto max-w-7xl px-6 py-10">
        <div className="grid gap-8 lg:grid-cols-[360px_1fr]">
          <aside className="rounded-2xl border border-[#dce5ea] bg-white p-7 shadow-[0_18px_45px_rgba(22,39,53,0.05)]">
            <UserAvatar user={user} size="lg" rounded="xl" />
            <h1 className="mt-6 text-3xl font-black tracking-[-0.04em]">{user.name}</h1>
            <p className="mt-2 break-all text-sm font-semibold text-[#65707b]">{user.email}</p>

            <div className="mt-7 rounded-xl bg-[#eafbff] p-5">
              <p className="text-xs font-black uppercase tracking-[0.16em] text-[#0aaed3]">Trips planned</p>
              <p className="mt-2 text-3xl font-black text-[#172033]">
                {loadingTrips ? '...' : tripsError ? 'Setup needed' : tripCount ?? 0}
              </p>
              <p className="mt-2 text-sm font-medium leading-6 text-[#65707b]">
                {tripsError ? 'Supabase history is not ready yet.' : 'Saved itineraries are stored in your Supabase-backed history.'}
              </p>
            </div>

            <button
              type="button"
              onClick={handleSignOut}
              className="mt-7 h-11 w-full rounded-lg border border-[#cfdbe2] bg-white text-sm font-black text-[#171b22] transition hover:border-red-200 hover:bg-red-50 hover:text-red-600"
            >
              Sign out
            </button>
          </aside>

          <section className="space-y-8">
            <div className="rounded-2xl border border-[#dce5ea] bg-white p-8 shadow-[0_18px_45px_rgba(22,39,53,0.05)]">
              <div className="flex flex-col justify-between gap-5 md:flex-row md:items-center">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.16em] text-[#21c8ee]">Profile</p>
                  <h2 className="mt-3 text-3xl font-black tracking-[-0.04em]">Your saved planning workspace</h2>
                  <p className="mt-3 max-w-2xl text-sm font-medium leading-6 text-[#65707b]">
                    Generate a verified itinerary, save it to history, and reopen it later without asking the backend
                    to recompute the trip.
                  </p>
                </div>
                <Link
                  href="/plan"
                  className="inline-flex h-12 items-center justify-center rounded-lg bg-[#21c8ee] px-6 text-sm font-black text-white shadow-[0_14px_28px_rgba(33,200,238,0.25)] transition hover:-translate-y-0.5 hover:bg-[#15bde5]"
                >
                  New Plan
                </Link>
              </div>
            </div>

            <div id="trip-history" className="rounded-2xl border border-[#dce5ea] bg-white p-8 shadow-[0_18px_45px_rgba(22,39,53,0.05)]">
              <div className="flex items-center justify-between gap-4">
                <h2 className="text-2xl font-black tracking-[-0.03em]">Recent saved trips</h2>
                <Link href="/history" className="text-sm font-black text-[#0aaed3] transition hover:text-[#087f99]">
                  View all
                </Link>
              </div>

              {loadingTrips ? (
                <div className="mt-6 rounded-xl border border-dashed border-[#cfdbe2] bg-[#fbfdfe] p-8 text-center text-sm font-bold text-[#65707b]">
                  Loading saved trips...
                </div>
              ) : tripsError ? (
                <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-8 text-amber-900">
                  <p className="text-sm font-black">History setup needs attention</p>
                  <p className="mt-2 text-sm font-bold leading-6">{tripsError}</p>
                  <p className="mt-2 text-sm font-medium leading-6">
                    Run `supabase/schema.sql` in Supabase SQL Editor before profile trip counts can load.
                  </p>
                </div>
              ) : recentTrips.length ? (
                <div className="mt-6 grid gap-4">
                  {recentTrips.map((trip) => (
                    <Link
                      key={trip.trip_id}
                      href={`/trips/${trip.trip_id}`}
                      className="rounded-xl border border-[#dce5ea] bg-[#fbfdfe] p-5 transition hover:-translate-y-0.5 hover:border-[#21c8ee] hover:bg-white hover:shadow-[0_16px_35px_rgba(22,39,53,0.08)]"
                    >
                      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
                        <div>
                          <p className="text-lg font-black tracking-[-0.02em] text-[#172033]">{trip.title || 'Saved itinerary'}</p>
                          <p className="mt-1 text-sm font-semibold text-[#657184]">
                            {trip.destination || 'Destination not specified'} | {formatDate(trip.created_at)}
                          </p>
                        </div>
                        <p className="text-sm font-black text-[#0aaed3]">
                          {trip.duration_days ? `${trip.duration_days} days` : 'Flexible'} |{' '}
                          {trip.budget_per_person ? `${formatCurrency(trip.budget_per_person)}/person` : 'Budget open'}
                        </p>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="mt-6 rounded-xl border border-dashed border-[#cfdbe2] bg-[#fbfdfe] p-8 text-center">
                  <p className="text-sm font-black text-[#171b22]">No saved trips yet</p>
                  <p className="mx-auto mt-2 max-w-md text-sm font-medium leading-6 text-[#65707b]">
                    Your Supabase-backed history will fill in after your first generated itinerary.
                  </p>
                </div>
              )}
            </div>
          </section>
        </div>
      </section>
    </main>
  )
}
