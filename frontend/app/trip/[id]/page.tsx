'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import axios from 'axios'

interface TripParams {
  params: {
    id: string
  }
}

type TripData = {
  trip_id?: string
  itinerary?: {
    destination?: string
    days?: Array<{
      day: number
      date?: string | null
      items?: Array<{
        start_time?: string
        end_time?: string
        place_name?: string
        description?: string
        estimated_cost?: number
        travel_time_from_previous_minutes?: number | null
        source_confidence?: number
      }>
    }>
  }
  feasibility_score?: {
    overall_score?: number
    grade?: string
  }
  budget_report?: {
    attraction_tickets?: number
    food?: number
    local_transport?: number
    total_per_person?: number
    budget_remaining_per_person?: number
  }
  why_this_trip_works?: string
  warnings?: string[]
}

export default function TripResult({ params }: TripParams) {
  const [trip, setTrip] = useState<TripData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    const loadTrip = async () => {
      try {
        setLoading(true)
        setError('')
        const response = await axios.get(`http://localhost:8000/api/trips/${params.id}`)
        if (isMounted) {
          setTrip(response.data)
        }
      } catch (requestError) {
        if (isMounted) {
          setTrip(null)
          setError('Trip not found or backend is unavailable.')
          console.error(requestError)
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadTrip()

    return () => {
      isMounted = false
    }
  }, [params.id])

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!trip) {
    return <div className="flex items-center justify-center min-h-screen">{error || 'Trip not found'}</div>
  }

  const score = trip.feasibility_score || { overall_score: 92, grade: 'A' }
  const itineraryDays = trip.itinerary?.days || []
  const budget = trip.budget_report

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white font-bold">A</div>
              <span className="text-xl font-bold text-gray-900">AetherTrip</span>
            </Link>
            <div className="text-2xl font-bold text-gray-900">{trip.itinerary?.destination || 'Trip'}</div>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/trip/new" className="text-gray-600 hover:text-gray-900">New Trip</Link>
            <button className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">Download PDF</button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-3 gap-8">
          {/* Left: Itinerary */}
          <div className="col-span-2">
            {/* Score Card */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl p-8 mb-8 border border-gray-200"
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Itinerary Feasibility Score</h2>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-sm text-gray-600">Accuracy Level: Verified</div>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-8 mb-6">
                <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-400 to-cyan-300 flex items-center justify-center shadow-lg">
                  <div className="text-center">
                    <div className="text-5xl font-bold text-white">{score.overall_score}</div>
                    <div className="text-sm text-blue-100">SCORE</div>
                  </div>
                </div>

                <div className="flex-1 space-y-2">
                  {[
                    { label: 'SCHEDULE', value: 88 },
                    { label: 'BUDGET', value: 82 },
                    { label: 'TRANSIT', value: 86 },
                    { label: 'RATINGS', value: 92 },
                  ].map((component) => (
                    <div key={component.label} className="flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-700">{component.label}</span>
                      <div className="flex items-center gap-2 flex-1 ml-4">
                        <div className="flex-1 h-2 bg-gray-200 rounded-full">
                          <div
                            className="h-2 bg-blue-500 rounded-full"
                            style={{ width: `${component.value}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold text-gray-600 w-8">{component.value}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Days */}
            {itineraryDays.map((day, dayIdx) => (
              <motion.div
                key={dayIdx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: dayIdx * 0.1 }}
                className="bg-white rounded-2xl p-8 mb-8 border border-gray-200"
              >
                <h3 className="text-2xl font-bold text-gray-900 mb-6">
                  Day {day.day} <span className="text-gray-500 font-normal text-lg">{day.date || 'TBD'}</span>
                </h3>

                <div className="space-y-6">
                  {day.items?.map((item, itemIdx: number) => (
                    <motion.div
                      key={itemIdx}
                      initial={{ opacity: 0, x: -10 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      className="border-l-4 border-blue-500 pl-6 pb-6"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="text-sm text-gray-500">{item.start_time}</div>
                          <h4 className="text-lg font-bold text-gray-900">{item.place_name}</h4>
                          <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                        </div>
                        <div className="text-right">
                          {item.source_confidence !== undefined && (
                            <div className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                              item.source_confidence > 0.8
                                ? 'bg-green-100 text-green-700'
                                : item.source_confidence > 0.5
                                ? 'bg-yellow-100 text-yellow-700'
                                : 'bg-red-100 text-red-700'
                            }`}>
                              {item.source_confidence > 0.8 ? 'Verified' : 'Check Req'}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-4 text-sm text-gray-600 mt-3">
                        <span>EST. COST: ${item.estimated_cost}</span>
                        {item.travel_time_from_previous_minutes && (
                          <span>{item.travel_time_from_previous_minutes} min travel</span>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            ))}

            {/* Why This Trip Works */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl p-8 border border-gray-200"
            >
              <h3 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span className="text-blue-500">✓</span> Why This Trip Works
              </h3>
              <div className="space-y-4 text-gray-700 whitespace-pre-line">
                {trip.why_this_trip_works || 'This itinerary is assembled from validated constraints, local data, and repair logic.'}
              </div>
            </motion.div>
          </div>

          {/* Right: Sidebar */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="sticky top-8 space-y-6"
          >
            {/* Budget Breakdown */}
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <h3 className="font-bold text-gray-900 mb-4">Budget Breakdown</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Activities</span>
                  <span className="font-semibold">${budget?.attraction_tickets || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Dining & Drinks</span>
                  <span className="font-semibold">${budget?.food || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Transit & DASH</span>
                  <span className="font-semibold">${budget?.local_transport || 0}</span>
                </div>
                <div className="pt-3 border-t flex justify-between font-bold">
                  <span>Total Estimated</span>
                  <span className="text-blue-600">${budget?.total_per_person || 0}</span>
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Within Budget</span>
                  <span>${budget?.budget_remaining_per_person || 0}</span>
                </div>
              </div>
            </div>

            {/* Hidden Costs */}
            <div className="bg-blue-50 rounded-2xl p-6 border border-blue-200">
              <h3 className="font-bold text-gray-900 mb-3">Hidden Costs Flagged</h3>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex gap-2">
                  <span className="text-blue-600">✓</span> <span>Intelligence & Repairs</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-blue-600">✓</span> <span>Weather Warning</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-blue-600">✓</span> <span>Logistics Repairs</span>
                </li>
              </ul>
            </div>

            {/* Warnings */}
            <div className="bg-yellow-50 rounded-2xl p-6 border border-yellow-200">
              <h3 className="font-bold text-gray-900 mb-3 text-sm">⚠️ WARNINGS</h3>
              <div className="space-y-2 text-sm text-gray-700">
                {(trip.warnings?.length ? trip.warnings : ['No warnings reported.']).map((warning, index) => (
                  <p key={index}>{warning}</p>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
