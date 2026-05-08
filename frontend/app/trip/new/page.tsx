'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import axios from 'axios'

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export default function NewTrip() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [chatPrompt, setChatPrompt] = useState(
    'Plan a 4-day trip from San Jose to Los Angeles for 4 travelers under $400 each. We want vegetarian food, no car, and a mix of museums and scenic stops.'
  )
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'Tell me your trip goals in one message. I will turn it into a verified plan and keep only the chatbot flow on this page.',
    },
  ])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatPrompt.trim()) {
      setErrorMessage('Type a trip request first.')
      return
    }

    setLoading(true)
    setErrorMessage('')
    
    try {
      const userInput = chatPrompt.trim()

      setMessages(prev => [
        ...prev,
        { role: 'user', content: userInput },
        { role: 'assistant', content: 'Planning your trip now...' },
      ])

      const response = await axios.post('http://localhost:8000/api/trips/plan', {
        user_input: userInput
      })
      
      router.push(`/trip/${response.data.trip_id}`)
    } catch (error) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || 'Unable to reach the planning API. Start the backend on port 8000 and try again.'
        : 'Error planning trip. Please try again.'
      setErrorMessage(message)
      setMessages(prev => [...prev.slice(0, -1), { role: 'assistant', content: message }])
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white text-slate-900">
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-500 text-sm font-bold text-white shadow-sm">
              A
            </div>
            <span className="text-lg font-semibold tracking-tight text-slate-900">AetherTrip</span>
          </div>
          <nav className="hidden items-center gap-10 text-sm font-medium text-slate-700 md:flex">
            <a href="#chat" className="transition hover:text-slate-950">Chat</a>
            <a href="#examples" className="transition hover:text-slate-950">Examples</a>
            <button className="transition hover:text-slate-950">Sign in</button>
            <a
              href="/trip/new"
              className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-600"
            >
              Plan a trip
            </a>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-5 pb-10 pt-12 sm:px-6 lg:px-8 lg:pt-16">
        <section className="mx-auto max-w-3xl text-center">
          <div className="inline-flex items-center rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold text-sky-600">
            Chat-Based Trip Planning
          </div>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
            Plan your trip in one chat message
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
            Tell AetherTrip where you want to go, your budget, style, and any constraints. The planner will extract the details from your chat and generate a verified itinerary.
          </p>
        </section>

        <section id="chat" className="mt-10 mx-auto grid max-w-4xl gap-6 lg:grid-cols-[1fr_0.72fr] lg:items-start">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
            className="rounded-3xl bg-white p-6 shadow-[0_12px_40px_rgba(15,23,42,0.08)] ring-1 ring-slate-200 sm:p-8"
          >
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-900">Chat with AetherTrip</h3>
                <textarea
                  value={chatPrompt}
                  onChange={(e) => setChatPrompt(e.target.value)}
                  placeholder="Plan a 4-day trip from San Jose to Los Angeles for 4 travelers under $400 each. We want vegetarian food, no car, and a mix of museums and scenic stops."
                  className="mt-3 min-h-[132px] w-full resize-none rounded-2xl border border-slate-200 bg-white px-4 py-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
                />
                <p className="mt-2 text-right text-xs text-slate-400">{chatPrompt.length} characters</p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-sky-500 px-5 py-3.5 text-sm font-semibold text-white shadow-[0_8px_24px_rgba(14,165,233,0.25)] transition hover:bg-sky-600 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {loading ? 'Generating itinerary...' : 'Generate itinerary'}
                {!loading && <span aria-hidden="true">⌕</span>}
              </button>

              {errorMessage && (
                <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {errorMessage}
                </div>
              )}
            </form>

            <div id="examples" className="mt-8">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Try these examples</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {[
                  'Plan a 3-day budget LA trip from San Jose for 4 friends.',
                  'Plan a no-car San Francisco weekend with museums and food.',
                  'Plan a vegetarian New York itinerary with hidden cost checks.',
                  'Plan a rain-safe Seattle trip with indoor backups.',
                  'Plan a family-friendly Tokyo week with transit only.',
                ].map(example => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => setChatPrompt(example)}
                    className="rounded-full border border-slate-200 px-4 py-2 text-xs font-medium text-slate-700 transition hover:border-sky-300 hover:bg-sky-50 hover:text-sky-700"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>

          <motion.aside
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.08 }}
            className="rounded-3xl bg-slate-950 p-6 text-white shadow-[0_12px_40px_rgba(15,23,42,0.18)] sm:p-8"
          >
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Chat Flow</h2>
              <div className="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-white/70">
                live
              </div>
            </div>

            <div className="mt-6 space-y-3 rounded-3xl border border-white/10 bg-white/5 p-4">
              {messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                    message.role === 'user'
                      ? 'ml-auto bg-sky-500 text-white'
                      : 'bg-white/10 text-white/90'
                  }`}
                >
                  {message.content}
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-3xl border border-white/10 bg-white/5 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-200">Prompt Tip</div>
              <p className="mt-2 text-sm leading-6 text-white/80">
                Include city, duration, travelers, budget, food preferences, transport mode, and anything you want avoided.
              </p>
            </div>
          </motion.aside>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-4 text-xs text-slate-500 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <p>© 2024 AetherTrip AI. Chat-first planning.</p>
          <div className="flex gap-5">
            <a href="#" className="transition hover:text-slate-800">Privacy</a>
            <a href="#" className="transition hover:text-slate-800">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
