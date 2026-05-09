'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import axios from 'axios'
import Link from 'next/link'

export default function NewTrip() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [tripDescription, setTripDescription] = useState(
    'Plan a 4-day trip from San Jose for 4 friends under $400 each, vegetarian, no car.'
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!tripDescription.trim()) return

    setLoading(true)
    
    try {
      const response = await axios.post('http://localhost:8000/api/trips/plan', {
        user_input: tripDescription.trim()
      })
      
      router.push(`/trip/${response.data.trip_id}?loading=true`)
    } catch (error) {
      console.error(error)
      setLoading(false)
    }
  }

  const verificationSteps = [
    { label: 'Understanding request', progress: 100 },
    { label: 'Extracting constraints', progress: 85 },
    { label: 'Fetching real places', progress: 0 },
    { label: 'Checking weather', progress: 0 },
    { label: 'Calculating travel times', progress: 0 },
    { label: 'Validating budget', progress: 0 },
    { label: 'Repairing if needed', progress: 0 },
    { label: 'Scoring feasibility', progress: 0 },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-cyan-500 rounded-lg flex items-center justify-center text-white font-bold">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9v-2h2v2zm0-4H9V5h2v4z"/>
                </svg>
              </div>
              <span className="text-xl font-bold text-gray-900">AetherTrip</span>
            </Link>
            <nav className="flex items-center gap-6 text-sm">
              <Link href="/trip/new" className="text-cyan-500 font-medium flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Plan
              </Link>
              <Link href="#" className="text-gray-600 hover:text-gray-900 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                History
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-green-600">98.4% Verified</span>
            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full"></div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-3 gap-8">
          {/* Left Column - Form */}
          <div className="col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              {/* Badge */}
              <div className="inline-flex items-center gap-2 bg-cyan-50 text-cyan-600 px-3 py-1 rounded-full text-xs font-semibold">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                VERIFIED PLANNING ENGINE
              </div>

              {/* Title */}
              <h1 className="text-5xl font-bold text-gray-900 leading-tight">
                Where would you like to go?
              </h1>

              {/* Description */}
              <p className="text-lg text-gray-600">
                Describe your perfect trip in plain English. AetherTrip cross-references routes, opening hours, and budgets in real-time.
              </p>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Trip Description */}
                <div className="bg-white rounded-2xl border border-gray-200 p-6">
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    TRIP DESCRIPTION
                  </label>
                  <textarea
                    value={tripDescription}
                    onChange={(e) => setTripDescription(e.target.value)}
                    className="w-full h-32 px-4 py-3 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-cyan-500 text-gray-700"
                    placeholder="Plan a 4-day trip from San Jose for 4 friends under $400 each, vegetarian, no car."
                  />
                  
                  {/* Quick Info */}
                  <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-xs text-gray-500 uppercase mb-1">Duration</div>
                      <div className="font-semibold text-gray-900">3 Days</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 uppercase mb-1">Budget</div>
                      <div className="font-semibold text-gray-900">$500pp</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 uppercase mb-1">Travelers</div>
                      <div className="font-semibold text-gray-900">4 Friends</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 uppercase mb-1">Diet</div>
                      <div className="font-semibold text-gray-900">Vegetarian</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 uppercase mb-1">Transport</div>
                      <div className="font-semibold text-gray-900">No Car</div>
                    </div>
                  </div>

                  {/* Preview Area */}
                  <div className="mt-6">
                    <div className="text-xs text-gray-500 uppercase mb-2">PREVIEW AREA</div>
                    <div className="relative h-48 bg-gray-100 rounded-lg overflow-hidden">
                      <img 
                        src="https://images.unsplash.com/photo-1534430480872-3498386e7856?w=800&auto=format&fit=crop"
                        alt="Route preview"
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent flex items-end p-4">
                        <div className="bg-white/90 backdrop-blur-sm px-3 py-2 rounded-lg text-sm font-medium text-gray-900">
                          📍 Route verified: San Jose → LA
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Example Chips */}
                <div>
                  <div className="text-xs font-semibold text-gray-500 uppercase mb-3">EXAMPLE CHIPS</div>
                  <div className="flex flex-wrap gap-2">
                    {[
                      'Budget LA trip',
                      'No-car San Francisco weekend',
                      'Vegetarian NYC itinerary',
                      'Rainy-safe Seattle trip',
                    ].map((chip) => (
                      <button
                        key={chip}
                        type="button"
                        onClick={() => setTripDescription(`Plan a ${chip.toLowerCase()} for 4 friends under $400 each.`)}
                        className="px-4 py-2 bg-gray-100 hover:bg-cyan-50 hover:text-cyan-600 rounded-full text-sm font-medium text-gray-700 transition-colors"
                      >
                        {chip}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Buttons */}
                <div className="flex gap-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 bg-cyan-500 hover:bg-cyan-600 text-white font-semibold py-4 px-6 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Generating...
                      </>
                    ) : (
                      <>
                        Generate Verified Itinerary
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    className="px-6 py-4 border-2 border-gray-200 hover:border-gray-300 rounded-xl font-semibold text-gray-700 transition-colors"
                  >
                    View sample itinerary
                  </button>
                </div>

                {/* Footer Note */}
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <svg className="w-4 h-4 text-cyan-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  Passed feasibility checks. Guaranteed with <span className="font-semibold">V2J</span> real-time sources.
                </div>
              </form>
            </motion.div>

            {/* Features Section */}
            <div className="mt-16 grid grid-cols-3 gap-8">
              {[
                {
                  icon: '🔧',
                  title: 'Automatic Repairs',
                  desc: 'If the AI finds a closed museum or a missed transit link, it repairs the itinerary automatically before showing it to you.',
                },
                {
                  icon: '📊',
                  title: 'Feasibility Scoring',
                  desc: 'Every plan gets a score from 0-100 based on route efficiency, budget buffer, and weather stability. Passed feasibility checks.',
                },
                {
                  icon: '🔍',
                  title: 'Trust Transparency',
                  desc: 'We clearly label "repaired" or "verified" states so you know exactly where your plan stands at all times.',
                },
              ].map((feature, i) => (
                <div key={i} className="text-center">
                  <div className="text-4xl mb-3">{feature.icon}</div>
                  <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-600">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column - Verification Engine */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-2xl border border-gray-200 p-6 sticky top-6"
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-gray-900">Verification Engine</h3>
                <span className="text-xs bg-cyan-100 text-cyan-600 px-2 py-1 rounded-full font-semibold">
                  v2.1 Live
                </span>
              </div>

              <p className="text-sm text-gray-600 mb-6">
                Real-time status of the AetherTrip 8 pipeline.
              </p>

              {/* Progress Steps */}
              <div className="space-y-4">
                {verificationSteps.map((step, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {step.progress === 100 ? (
                          <div className="w-5 h-5 bg-cyan-500 rounded-full flex items-center justify-center">
                            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </div>
                        ) : step.progress > 0 ? (
                          <div className="w-5 h-5 border-2 border-cyan-500 rounded-full flex items-center justify-center">
                            <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse"></div>
                          </div>
                        ) : (
                          <div className="w-5 h-5 border-2 border-gray-200 rounded-full"></div>
                        )}
                        <span className={`text-sm font-medium ${step.progress > 0 ? 'text-gray-900' : 'text-gray-400'}`}>
                          {step.label}
                        </span>
                      </div>
                      <span className={`text-sm font-semibold ${step.progress === 100 ? 'text-cyan-600' : step.progress > 0 ? 'text-cyan-500' : 'text-gray-300'}`}>
                        {step.progress}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Overall Progress */}
              <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-500 uppercase">Overall Progress</span>
                  <span className="text-sm font-bold text-cyan-600">43.8% Complete</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full" style={{ width: '43.8%' }}></div>
                </div>
              </div>
            </motion.div>

            {/* Trusted Data Sources */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl border border-gray-200 p-6"
            >
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-5 h-5 text-cyan-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <h3 className="font-bold text-gray-900">TRUSTED DATA SOURCES</h3>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {[
                  { name: 'Google Maps', icon: '🗺️' },
                  { name: 'NOAA Weather', icon: '🌤️' },
                  { name: 'OpenTable API', icon: '🍽️' },
                  { name: 'Skyscanner', icon: '✈️' },
                ].map((source, i) => (
                  <div key={i} className="flex items-center gap-2 bg-gray-50 rounded-lg p-3">
                    <span className="text-xl">{source.icon}</span>
                    <span className="text-xs font-medium text-gray-700">{source.name}</span>
                  </div>
                ))}
              </div>

              <p className="mt-4 text-xs text-gray-500">
                AetherTrip uses only reputable V2J headless APIs to verify decision-critical current pricing, live transit delays. Continuously by <span className="font-semibold">JD</span> Accuracy sources.
              </p>
            </motion.div>

            {/* Accuracy Guarantee */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-2xl border border-cyan-200 p-6"
            >
              <div className="flex items-center gap-2 mb-3">
                <svg className="w-5 h-5 text-cyan-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <h3 className="font-bold text-gray-900">Accuracy Guarantee</h3>
              </div>
              <p className="text-sm text-gray-700">
                Our model is constrained by real-world physics. We won't suggest a flight despite before you land.
              </p>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-20">
        <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-cyan-500 rounded-lg flex items-center justify-center text-white font-bold">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9v-2h2v2zm0-4H9V5h2v4z"/>
                </svg>
              </div>
              <span className="font-bold text-gray-900">AetherTrip</span>
            </div>
            <p className="text-sm text-gray-600">
              Accuracy-first travel planning engine. We don't just plan, we verify and repair.
            </p>
            <p className="text-xs text-gray-500 mt-4">
              © 2024 AetherTrip AI. Verified itineraries.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Technology</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-cyan-600">Feasibility Engine</a></li>
              <li><a href="#" className="hover:text-cyan-600">Route Repair</a></li>
              <li><a href="#" className="hover:text-cyan-600">Trust Status</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Legal</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-cyan-600">Terms of Verification</a></li>
              <li><a href="#" className="hover:text-cyan-600">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-cyan-600">Accuracy Disclaimer</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Status</h4>
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-green-600 font-semibold">Systems Verified</span>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              © 2024 AetherTrip AI. Verified itineraries.
            </p>
          </div>
        </div>
      </footer>

      {/* Made with Visily Badge */}
      <div className="fixed bottom-4 left-4 bg-white rounded-lg shadow-lg px-3 py-2 text-xs text-gray-600 flex items-center gap-2">
        Made with <span className="font-semibold text-purple-600">Visily</span>
      </div>
    </div>
  )
}
