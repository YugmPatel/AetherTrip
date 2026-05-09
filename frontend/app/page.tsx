'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-cyan-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9v-2h2v2zm0-4H9V5h2v4z"/>
              </svg>
            </div>
            <span className="text-lg font-bold text-gray-900">AetherTrip</span>
          </Link>
          <nav className="flex items-center gap-4">
            <a href="#" className="text-sm text-gray-600 hover:text-gray-900">Learn</a>
            <Link 
              href="/trip/new" 
              className="bg-cyan-400 hover:bg-cyan-500 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              New Plan
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-gray-50 to-cyan-50/30">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="grid grid-cols-2 gap-16 items-start">
            {/* Left Column */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="inline-block bg-cyan-100 text-cyan-600 px-3 py-1.5 rounded-full text-xs font-semibold mb-6">
                ✓ BUILT FOR TRAVEL CLARITY
              </div>
              
              <h1 className="text-5xl font-bold mb-6 leading-tight text-gray-900">
                AI travel plans that are <span className="text-cyan-500">verified</span> before you trust them.
              </h1>
              
              <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                AetherTrip checks routes, opening hours, budget, weather, and hidden costs—then repairs broken itineraries automatically.
              </p>

              <div className="flex gap-4 mb-10">
                <Link 
                  href="/trip/new"
                  className="bg-cyan-400 hover:bg-cyan-500 text-white px-7 py-3.5 rounded-xl font-semibold transition-colors"
                >
                  Plan a trip
                </Link>
                <button className="border-2 border-gray-300 hover:border-gray-400 text-gray-700 px-7 py-3.5 rounded-xl font-semibold transition-colors">
                  View sample itinerary
                </button>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="w-9 h-9 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full border-2 border-white"
                    />
                  ))}
                </div>
                <p className="text-sm text-gray-600">Trusted by global travelers</p>
              </div>
            </motion.div>

            {/* Right Column - Verification Card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <div className="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-3xl p-7 border border-cyan-100 shadow-lg">
                {/* Trip Header */}
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-1">Tokyo 4-Days • First</h3>
                    <p className="text-xs text-gray-500">Oct 14 - Oct 18, 2024 • 5 Days</p>
                  </div>
                  <button className="text-gray-400 hover:text-gray-600">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
                    </svg>
                  </button>
                </div>

                {/* Score Circle */}
                <div className="flex items-center justify-center mb-6">
                  <div className="relative">
                    <svg className="w-36 h-36 transform -rotate-90">
                      <circle
                        cx="72"
                        cy="72"
                        r="64"
                        stroke="#e5e7eb"
                        strokeWidth="10"
                        fill="none"
                      />
                      <circle
                        cx="72"
                        cy="72"
                        r="64"
                        stroke="#22d3ee"
                        strokeWidth="10"
                        fill="none"
                        strokeDasharray={`${2 * Math.PI * 64 * 0.92} ${2 * Math.PI * 64}`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-5xl font-bold text-gray-900">92</div>
                        <div className="text-sm text-gray-500 mt-1">/ 100</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Verification Metrics */}
                <div className="bg-white rounded-2xl p-5 mb-4 shadow-sm">
                  <h4 className="text-xs font-bold text-gray-500 mb-4 uppercase tracking-wide">Verification Metrics</h4>
                  <div className="space-y-3.5">
                    {[
                      { label: 'Opening Hours', value: 100, color: 'bg-green-500' },
                      { label: 'Travel Times', value: 95, color: 'bg-cyan-400' },
                      { label: 'Budget Sync', value: 87, color: 'bg-blue-500' },
                    ].map((metric, i) => (
                      <div key={i}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-medium text-gray-700">{metric.label}</span>
                          <span className="text-xs font-bold text-gray-900">{metric.value}%</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${metric.color} rounded-full transition-all duration-500`}
                            style={{ width: `${metric.value}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Instant Fixes Applied */}
                <div className="bg-white rounded-2xl p-4 mb-3 shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-cyan-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                    </svg>
                    <h4 className="text-xs font-bold text-gray-600 uppercase">Instant Fixes Applied</h4>
                  </div>
                  <p className="text-xs text-gray-600 leading-relaxed">
                    Museum closed on Monday? We auto-shifted your schedule to Tuesday and verified the new route.
                  </p>
                </div>

                {/* AI Co-Traveler */}
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl p-4 border border-purple-100 shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full"></div>
                    <h4 className="text-xs font-bold text-gray-900">AI Co-Traveler</h4>
                    <span className="ml-auto text-xs text-cyan-600 font-bold">✓ LIVE</span>
                  </div>
                  <p className="text-xs text-gray-600">
                    Need a last-minute change? Ask me anything.
                  </p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-white py-14 border-y">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-4 gap-8 text-center">
            {[
              { value: '99.8%', label: 'TRIP ACCURACY' },
              { value: '140+', label: 'REAL-TIME SOURCES' },
              { value: '2.1M', label: 'AI VERIFICATIONS' },
              { value: '4.9/5', label: 'TRUST SCORE' },
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="text-4xl font-bold text-gray-900 mb-2">{stat.value}</div>
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* The 8-Layer Verification Engine */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">The 8-Layer Verification Engine</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              We don't just generate plans. Every itinerary passes through eight stages of real-world<br />fact-checking to ensure accuracy and feasibility.
            </p>
          </div>

          <div className="grid grid-cols-4 gap-6">
            {[
              {
                icon: '🔍',
                title: 'Route Logic',
                desc: 'Checks actual travel times between locations using real traffic and transit data.',
              },
              {
                icon: '🕐',
                title: 'Live Hours',
                desc: 'Verifies opening and closing times so you\'re never stuck at a closed museum.',
              },
              {
                icon: '💰',
                title: 'Hidden Costs',
                desc: 'Calculates taxes, tips and fees so your budget is 100% accurate.',
              },
              {
                icon: '🌤️',
                title: 'Climate Sync',
                desc: 'Monitors historical weather patterns to suggest the best time to visit.',
              },
              {
                icon: '✅',
                title: 'Trust Scoring',
                desc: 'Assigns a 0-100 reliability score so you know exactly how solid your plan is.',
              },
              {
                icon: '🔧',
                title: 'Auto-Repair',
                desc: 'If a conflict is found, our system automatically fixes the issue in real-time.',
              },
              {
                icon: '📍',
                title: 'Place Audit',
                desc: 'Cross-references official data to verify locations are currently open and active.',
              },
              {
                icon: '🎯',
                title: 'Instant Feasibility',
                desc: 'Get a real-time viability report so you can book with confidence.',
              },
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.05 }}
                viewport={{ once: true }}
                className="bg-white rounded-2xl p-6 border border-gray-200 hover:border-cyan-300 hover:shadow-md transition-all"
              >
                <div className="text-4xl mb-3">{feature.icon}</div>
                <h3 className="text-base font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Our AI doesn't just plan. It fixes what's broken. */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-4xl font-bold text-gray-900 mb-8 leading-tight">
                Our AI doesn't just plan.<br />It fixes what's broken.
              </h2>

              <div className="space-y-6">
                {[
                  {
                    icon: '✓',
                    title: 'Verification Over Generation',
                    desc: 'Traditional AI "hallucinates" hotel prices, opening hours, or even fake locations. We cross-check every detail.',
                  },
                  {
                    icon: '🔄',
                    title: 'Dynamic Repair Cycles',
                    desc: 'If the AI finds a conflict (e.g., a flight is delayed or a place is closed), it automatically re-plans your itinerary.',
                  },
                  {
                    icon: '💎',
                    title: 'Budget-First Constraints',
                    desc: 'Every spend is tied to real-world data and verified against your budget with emergency buffers built in.',
                  },
                ].map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, delay: i * 0.1 }}
                    viewport={{ once: true }}
                    className="flex gap-4"
                  >
                    <div className="flex-shrink-0 w-8 h-8 bg-cyan-100 rounded-full flex items-center justify-center text-cyan-600 font-bold text-sm">
                      {item.icon}
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900 mb-1.5">{item.title}</h3>
                      <p className="text-sm text-gray-600 leading-relaxed">{item.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>

              <button className="mt-8 text-cyan-500 font-semibold hover:text-cyan-600 flex items-center gap-2 text-sm">
                Explore the flow
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="bg-slate-800 rounded-3xl p-8 text-white shadow-xl"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold">Live Verification Dashboard</h3>
                <span className="bg-green-500 text-white text-xs px-2.5 py-1 rounded-full font-semibold">ACTIVE</span>
              </div>

              <div className="space-y-4 mb-6">
                <div className="bg-white/10 backdrop-blur rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Route Feasibility</span>
                    <span className="text-cyan-400 font-bold text-sm">98%</span>
                  </div>
                  <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-cyan-400 rounded-full" style={{ width: '98%' }}></div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Budget Accuracy</span>
                    <span className="text-green-400 font-bold text-sm">100%</span>
                  </div>
                  <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-green-400 rounded-full" style={{ width: '100%' }}></div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Weather Stability</span>
                    <span className="text-blue-400 font-bold text-sm">85%</span>
                  </div>
                  <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-400 rounded-full" style={{ width: '85%' }}></div>
                  </div>
                </div>
              </div>

              <div className="bg-cyan-500/20 border border-cyan-400/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-5 h-5 text-cyan-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <h4 className="font-semibold text-cyan-300 text-sm">Real-time Fixes</h4>
                </div>
                <p className="text-sm text-gray-300">
                  Backup plan auto-created
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
              Ready for a trip that actually works?
            </h2>
            <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
              Join thousands of travelers who have swapped hallucinations for verified, high-feasibility itineraries. No surprises, just real plans.
            </p>
            <Link 
              href="/trip/new"
              className="inline-block bg-cyan-400 hover:bg-cyan-500 text-white px-10 py-4 rounded-xl font-semibold text-lg transition-colors shadow-lg shadow-cyan-200"
            >
              Start My Verified Plan →
            </Link>
            <p className="mt-5 text-sm text-gray-500">
              ✓ No credit card required • API
            </p>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-cyan-500 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11H9v-2h2v2zm0-4H9V5h2v4z"/>
                  </svg>
                </div>
                <span className="font-bold text-gray-900">AetherTrip</span>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                Accuracy-first travel planning engine. We don't just plan, we verify and repair.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4 text-sm">Technology</h4>
              <ul className="space-y-2.5 text-sm text-gray-600">
                <li><a href="#" className="hover:text-cyan-600">Feasibility Engine</a></li>
                <li><a href="#" className="hover:text-cyan-600">Route Repair</a></li>
                <li><a href="#" className="hover:text-cyan-600">Trust Status</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4 text-sm">Legal</h4>
              <ul className="space-y-2.5 text-sm text-gray-600">
                <li><a href="#" className="hover:text-cyan-600">Terms of Verification</a></li>
                <li><a href="#" className="hover:text-cyan-600">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-cyan-600">Accuracy Disclaimer</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4 text-sm">Status</h4>
              <div className="flex items-center gap-2 text-sm mb-3">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-600 font-semibold">Systems Verified</span>
              </div>
              <p className="text-xs text-gray-500">
                All verification engines operational
              </p>
            </div>
          </div>
          <div className="border-t pt-6 text-center text-sm text-gray-500">
            © 2024 AetherTrip AI. Verified itineraries.
          </div>
        </div>
      </footer>

      {/* Made with Visily Badge */}
      <div className="fixed bottom-4 left-4 bg-white rounded-lg shadow-lg px-3 py-2 text-xs text-gray-600 flex items-center gap-1.5 border border-gray-200">
        Made with <span className="font-semibold text-purple-600 flex items-center gap-1">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
          </svg>
          Visily
        </span>
      </div>
    </div>
  )
}
