'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import AgentProgress from '@/components/AgentProgress'
import Footer from '@/components/Footer'
import Header from '@/components/Header'
import TripInputForm from '@/components/TripInputForm'
import { streamPlanTrip } from '@/lib/api'
import { PipelineEvent } from '@/lib/types'
import { storeTrip, storeTripNotice } from '@/lib/utils'
import { useAuthSession } from '@/lib/auth'
import { saveTripToSupabase } from '@/lib/trip-storage'

const sources = ['Geoapify Places', 'OpenRouteService', 'Open-Meteo', 'Wikidata/Wikipedia']

function DataSourceCards() {
  return (
    <div className="mt-8 grid gap-6 lg:grid-cols-2">
      <section className="rounded-2xl border border-cyan-100 bg-[#eafbff] p-7">
        <h2 className="text-sm font-black uppercase tracking-[0.14em] text-[#21c8ee]">Trusted Data Sources</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {sources.map((source) => (
            <div key={source} className="rounded-xl border border-[#d7e8f0] bg-white px-4 py-4 text-sm font-black text-[#405268] shadow-[0_8px_18px_rgba(22,39,53,0.06)]">
              {source}
            </div>
          ))}
        </div>
        <p className="mt-6 text-xs font-semibold italic leading-5 text-[#61758b]">
          AetherTrip uses the backend services actually configured for place grounding, routing, weather, and knowledge checks.
        </p>
      </section>

      <section className="rounded-2xl border border-dashed border-[#cbdbe6] bg-white/75 p-7">
        <div className="flex gap-5">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} viewBox="0 0 24 24">
              <path d="M12 3 5.5 5.7v5.8c0 4.1 2.7 7.8 6.5 9.1 3.8-1.3 6.5-5 6.5-9.1V5.7L12 3Z" />
              <path d="m9.4 12.1 1.7 1.7 3.7-4.1" />
            </svg>
          </span>
          <div>
            <h2 className="text-lg font-black tracking-[-0.02em] text-[#172033]">Accuracy Note</h2>
            <p className="mt-3 text-sm font-medium leading-6 text-[#61758b]">
              AetherTrip validates against real-world constraints at generation time, but does not guarantee future
              availability, pricing, closures, weather, or route changes.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}

function FeatureCards() {
  const features = [
    {
      title: 'Automatic Repairs',
      description:
        'If validation finds a closed venue or impossible route, AetherTrip can repair the itinerary before showing it.',
    },
    {
      title: 'Feasibility Scoring',
      description:
        'Every plan receives a score based on route logic, budget stability, source confidence, and validation checks.',
    },
    {
      title: 'Trust Transparency',
      description:
        'Warnings, repairs, low-confidence items, and source details stay visible instead of being hidden.',
    },
  ]

  return (
    <section className="border-t border-[#dce5ea] bg-[#f7fafc]">
      <div className="mx-auto grid max-w-[1180px] gap-10 px-5 py-20 sm:px-8 md:grid-cols-3">
        {features.map((feature) => (
          <article key={feature.title}>
            <span className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-white text-[#21c8ee] shadow-[0_10px_24px_rgba(22,39,53,0.08)]">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} viewBox="0 0 24 24">
                <path d="m5 12 4 4 10-10" />
              </svg>
            </span>
            <h3 className="text-xl font-black tracking-[-0.03em] text-[#172033]">{feature.title}</h3>
            <p className="mt-4 text-sm font-medium leading-6 text-[#61758b]">{feature.description}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

export default function PlanPage() {
  const router = useRouter()
  const { user, hydrated } = useAuthSession()
  const [events, setEvents] = useState<PipelineEvent[]>([])
  const [isPlanning, setIsPlanning] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(prompt: string) {
    if (!hydrated) {
      setError('Checking your session. Please try again in a moment.')
      return
    }

    if (!prompt.trim()) {
      setError('Tell AetherTrip where you want to go before generating an itinerary.')
      return
    }

    setError('')
    setEvents([])
    setIsPlanning(true)

    try {
      const originalPrompt = prompt.trim()
      const trip = await streamPlanTrip(originalPrompt, (event) => {
        setEvents((current) => [...current, event])
      })
      storeTrip(trip)

      if (user) {
        try {
          const saveResult = await saveTripToSupabase(trip, originalPrompt)
          if (saveResult.saved) {
            storeTripNotice(trip.trip_id, { type: 'success', message: 'Trip saved to history.' })
          } else if (saveResult.reason === 'not_authenticated') {
            storeTripNotice(trip.trip_id, { type: 'info', message: 'Sign in to save this trip.' })
          } else {
            console.warn('Supabase trip save failed', {
              reason: saveResult.reason,
              code: saveResult.code,
              message: saveResult.error,
            })
            storeTripNotice(trip.trip_id, {
              type: 'warning',
              message: 'Trip generated, but saving to history failed.',
            })
          }
        } catch (saveError) {
          console.warn('Supabase trip save threw', {
            message: saveError instanceof Error ? saveError.message : 'Unknown save error',
          })
          storeTripNotice(trip.trip_id, {
            type: 'warning',
            message: 'Trip generated, but saving to history failed.',
          })
        }
      } else {
        storeTripNotice(trip.trip_id, { type: 'info', message: 'Sign in to save this trip.' })
      }

      router.push(`/trips/${trip.trip_id}`)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Trip planning failed.')
      setIsPlanning(false)
    }
  }

  return (
    <main className="min-h-screen bg-white text-[#172033]">
      <Header />
      {isPlanning ? (
        <AgentProgress events={events} />
      ) : (
        <>
          <section className="relative overflow-hidden bg-[linear-gradient(110deg,#f1fdff_0%,#ffffff_42%,#f8fbff_100%)]">
            <div className="mx-auto max-w-[980px] px-5 py-16 sm:px-8 md:py-20">
              <div className="mb-9">
                <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-[#dff9fd] px-4 py-1.5 text-xs font-black uppercase tracking-[0.14em] text-[#15bee6]">
                  <span className="text-base leading-none">+</span>
                  Verified Planning Engine
                </div>
                <h1 className="text-[42px] font-black leading-tight tracking-[-0.055em] md:text-[56px]">
                  Where would you like to go?
                </h1>
                <p className="mt-5 max-w-[720px] text-lg font-medium leading-8 text-[#62748c]">
                  Describe your perfect trip in plain English. AetherTrip cross-references routes, opening hours, and
                  budgets in real-time.
                </p>
              </div>

              <TripInputForm onSubmit={handleSubmit} loading={isPlanning} error={error} />
              <DataSourceCards />
            </div>
          </section>
          <FeatureCards />
          <Footer />
        </>
      )}
    </main>
  )
}
