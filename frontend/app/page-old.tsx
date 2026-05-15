'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white font-bold">A</div>
            <span className="text-xl font-bold text-gray-900">AetherTrip</span>
          </div>
          <nav className="flex items-center gap-8">
            <a href="#" className="text-gray-600 hover:text-gray-900">How it works</a>
            <a href="#" className="text-gray-600 hover:text-gray-900">Sample Trip</a>
            <button className="text-gray-600 hover:text-gray-900">Sign in</button>
            <Link href="/plan" className="btn-primary">
              Plan a trip
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 grid grid-cols-2 gap-12 items-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-block bg-blue-100 text-blue-600 px-4 py-1 rounded-full text-sm font-semibold mb-6">
            Accuracy-First AI Travel
          </div>
          <h1 className="text-6xl font-bold mb-6 leading-tight">
            AI travel plans that are <span className="text-blue-500">verified</span> before you trust them.
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            AetherTrip checks routes, opening hours, budget, weather, and hidden costs—then repairs broken itineraries automatically. Experience zero-hallucination planning.
          </p>
          <div className="flex gap-4">
            <Link href="/plan" className="btn-primary">
              Plan a trip
            </Link>
            <button className="btn-secondary">
              View sample itinerary
            </button>
          </div>
          <div className="mt-12 flex items-center gap-4">
            <div className="flex -space-x-3">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="w-10 h-10 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-full border-2 border-white"
                />
              ))}
            </div>
            <p className="text-sm text-gray-600">5,000+ travelers verified their itineraries this month</p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="relative"
        >
          <div className="bg-white rounded-3xl shadow-2xl p-8 border border-gray-200">
            <div className="inline-block bg-green-100 text-green-600 px-3 py-1 rounded-full text-sm font-semibold mb-4">
              SCORE AUDIT
            </div>
            <div className="mb-8">
              <div className="text-6xl font-bold text-center text-gray-900 mb-2">92</div>
              <div className="text-center text-gray-600">Itinerary Verified</div>
              <p className="text-xs text-gray-500 text-center mt-2">This plan passes 82% of our feasibility criteria</p>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium">Opening hours verified</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium">Route travel times checked</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-yellow-500 rounded-full"></div>
                <span className="text-sm font-medium">Weather forecast sync</span>
              </div>
            </div>
            <button className="mt-6 w-full py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition">
              Update
            </button>
          </div>
        </motion.div>
      </section>

      {/* Stats Section */}
      <section className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-4 gap-8">
        {[
          { value: '92%', label: 'AVERAGE FEASIBILITY' },
          { value: '14k+', label: 'TRIPS AUTO-REPAIRED' },
          { value: '0', label: 'HALLUCINATED PLACES' },
          { value: '200+', label: 'LIVE DATA SOURCES' },
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: i * 0.1 }}
            className="text-center"
          >
            <div className="text-4xl font-bold text-gray-900">{stat.value}</div>
            <div className="text-xs text-gray-500 uppercase tracking-wide mt-2">{stat.label}</div>
          </motion.div>
        ))}
      </section>

      {/* Features Section */}
      <section className="bg-white py-20 border-t">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-bold mb-4">Built to solve the "AI Hallucination" problem in travel.</h2>
            <p className="text-xl text-gray-600">
              Traditional AI plans look great until you try to use them. AetherTrip treats every itinerary as a set of logical constraints to be solved.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-12">
            {[
              {
                icon: '🗺️',
                title: 'Verified route and timing',
                desc: 'We cross-reference real traffic data and public transit schedules to ensure travel between stops is physically possible.',
              },
              {
                icon: '💰',
                title: 'Accurate budget with hidden costs',
                desc: 'Forget estimated ranges. We calculate exact entry fees, estimated taxes, and common hidden costs like tips or parking.',
              },
              {
                icon: '⚙️',
                title: 'Auto-repair engine',
                desc: 'If a museum is closed on Mondays or a flight is delayed, our engine automatically shifts your schedule to find the next best path.',
              },
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-gray-600">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-slate-900 text-white py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-5xl font-bold mb-4">Stop trusting AI hallucinations. Start verified traveling.</h2>
          <p className="text-xl text-gray-300 mb-8">
            Join thousands of travelers who have eliminated planning stress and "place-closed" surprises with our AI co-pilot.
          </p>
          <div className="flex justify-center gap-4">
            <Link href="/plan" className="px-8 py-3 bg-blue-500 hover:bg-blue-600 rounded-lg font-semibold transition">
              Create your itinerary
            </Link>
            <button className="px-8 py-3 border-2 border-white hover:bg-white hover:text-slate-900 rounded-lg font-semibold transition">
              Watch Demo
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t">
        <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-4 gap-8">
          <div>
            <div className="font-bold mb-4">AetherTrip</div>
            <p className="text-sm text-gray-600">The world's first AI co-pilot that verifies routes, costs, and weather before you book.</p>
          </div>
          <div>
            <h4 className="font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-gray-900">Verification Engine</a></li>
              <li><a href="#" className="hover:text-gray-900">Auto-Repair</a></li>
              <li><a href="#" className="hover:text-gray-900">Pricing</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-gray-900">Sample Trips</a></li>
              <li><a href="#" className="hover:text-gray-900">How it works</a></li>
              <li><a href="#" className="hover:text-gray-900">Support</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-4">Connect</h4>
            <div className="flex gap-4 text-sm text-gray-600">
              <a href="#" className="hover:text-gray-900">Twitter</a>
              <a href="#" className="hover:text-gray-900">LinkedIn</a>
              <a href="#" className="hover:text-gray-900">GitHub</a>
            </div>
          </div>
        </div>
        <div className="border-t text-center py-6 text-sm text-gray-600">
          © 2024 AetherTrip AI. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
