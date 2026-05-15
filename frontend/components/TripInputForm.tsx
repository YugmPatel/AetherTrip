'use client'

import { useState } from 'react'

type TripInputFormProps = {
  onSubmit: (prompt: string) => void
  loading?: boolean
  error?: string
  generatedOutput?: string
}

const quickPrompts = [
  'Budget LA trip',
  'No-car San Francisco weekend',
  'Vegetarian NYC itinerary',
  'Rain-safe Seattle trip',
]

function SparkleIcon() {
  return (
    <svg
      className="h-5 w-5"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      viewBox="0 0 24 24"
      aria-hidden
    >
      <path d="m12 3 1.7 4.8L19 9.5l-5.3 1.7L12 16l-1.7-4.8L5 9.5l5.3-1.7L12 3Z" />
      <path d="m19 14 .8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8L19 14Z" />
    </svg>
  )
}

export default function TripInputForm({ onSubmit, loading, error, generatedOutput }: TripInputFormProps) {
  const [prompt, setPrompt] = useState('')
  const [copySuccess, setCopySuccess] = useState(false)
  const [copyError, setCopyError] = useState('')

  const handleCopyToClipboard = async () => {
    if (!generatedOutput) {
      return
    }

    if (typeof navigator === 'undefined' || !navigator.clipboard?.writeText) {
      setCopyError('Clipboard copy is not supported in this browser.')
      return
    }

    try {
      await navigator.clipboard.writeText(generatedOutput)
      setCopyError('')
      setCopySuccess(true)
      window.setTimeout(() => setCopySuccess(false), 2000)
    } catch {
      setCopySuccess(false)
      setCopyError('Unable to copy output.')
    }
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSubmit(prompt)
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-[20px] border border-[#d7e8f0] bg-white/88 p-7 shadow-[0_24px_80px_rgba(31,89,115,0.15)] backdrop-blur md:p-9"
    >
      <label className="block">
        <span className="mb-3 block text-xs font-black uppercase tracking-[0.11em] text-[#72849a]">
          Trip Preferences
        </span>
        <span className="relative block">
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            disabled={loading}
            rows={6}
            placeholder="Plan a 4-day Tokyo food and culture trip under $1,800, with public transit and one rainy-day backup."
            className="min-h-[170px] w-full resize-y rounded-xl border border-[#d6e4ec] bg-[#f8fdff] px-5 py-4 pr-12 text-base font-medium leading-7 text-[#172033] outline-none transition placeholder:text-[#9aa8ba] focus:border-[#21c8ee] focus:bg-white focus:ring-4 focus:ring-cyan-100 disabled:cursor-not-allowed disabled:opacity-70"
          />
          <span className="pointer-events-none absolute right-4 top-4 text-[#67d7ee]">
            <SparkleIcon />
          </span>
        </span>
      </label>

      {generatedOutput ? (
        <div className="mt-3 flex items-center gap-3">
          <button
            type="button"
            onClick={handleCopyToClipboard}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
          >
            {copySuccess ? 'Copied' : 'Copy output'}
          </button>

          {copyError ? <span className="text-sm text-red-600">{copyError}</span> : null}
        </div>
      ) : null}

      <div className="mt-7">
        <p className="mb-3 text-xs font-black uppercase tracking-[0.11em] text-[#9aa8ba]">Quick Prompts</p>
        <div className="flex flex-wrap gap-3">
          {quickPrompts.map((chip) => (
            <button
              key={chip}
              type="button"
              onClick={() => setPrompt(chip)}
              disabled={loading}
              className="rounded-full border border-[#d7e2ec] bg-white px-4 py-2 text-sm font-bold text-[#4e5d70] transition hover:-translate-y-0.5 hover:border-[#21c8ee] hover:text-[#0aaed3] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">
          {error}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={loading}
        className="mt-8 flex h-16 w-full items-center justify-center gap-3 rounded-xl bg-[#19aee6] text-lg font-black text-white shadow-[0_18px_35px_rgba(25,174,230,0.28)] transition hover:-translate-y-0.5 hover:bg-[#129fd4] disabled:cursor-not-allowed disabled:opacity-70"
      >
        {loading ? 'Generating Verified Itinerary' : 'Generate Verified Itinerary'}
        <svg
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          viewBox="0 0 24 24"
          aria-hidden
        >
          <path d="M12 3 5.5 5.7v5.8c0 4.1 2.7 7.8 6.5 9.1 3.8-1.3 6.5-5 6.5-9.1V5.7L12 3Z" />
          <path d="m9.4 12.1 1.7 1.7 3.7-4.1" />
        </svg>
      </button>

      <p className="mt-6 flex items-center justify-center gap-2 text-sm font-medium text-[#657184]">
        <span className="flex h-4 w-4 items-center justify-center rounded-full border border-emerald-400 text-emerald-500">
          <svg
            className="h-2.5 w-2.5"
            fill="none"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2.5}
            viewBox="0 0 24 24"
            aria-hidden
          >
            <path d="m5 12 4 4 10-10" />
          </svg>
        </span>
        Passed feasibility checks. Cross-referenced with real-time sources.
      </p>
    </form>
  )
}
