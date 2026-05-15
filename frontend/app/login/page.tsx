'use client'

import Link from 'next/link'
import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { getSafeNextPath } from '@/lib/auth'
import { createBrowserSupabaseClient } from '@/lib/supabase/client'

function GoogleIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden>
      <path fill="#4285F4" d="M22.6 12.2c0-.8-.1-1.5-.2-2.2H12v4.2h5.9c-.3 1.3-1 2.4-2.1 3.1v2.6h3.4c2-1.8 3.4-4.5 3.4-7.7Z" />
      <path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.8l-3.4-2.6c-.9.6-2.2 1-3.9 1-3 0-5.6-2-6.5-4.8H2v2.7C3.8 20.3 7.6 23 12 23Z" />
      <path fill="#FBBC05" d="M5.5 13.8a6.6 6.6 0 0 1 0-4.2V6.9H2a11 11 0 0 0 0 10l3.5-3.1Z" />
      <path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.3 1.7l3-3A10.3 10.3 0 0 0 12 1C7.6 1 3.8 3.7 2 6.9l3.5 2.7C6.4 7.4 9 5.4 12 5.4Z" />
    </svg>
  )
}

function MailIcon() {
  return (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} viewBox="0 0 24 24" aria-hidden>
      <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v11a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 17.5v-11Z" />
      <path d="m5 7 7 6 7-6" />
    </svg>
  )
}

function LoginForm() {
  const searchParams = useSearchParams()
  const nextPath = getSafeNextPath(searchParams.get('next'))
  const [email, setEmail] = useState('')
  const [error, setError] = useState(
    searchParams.get('error') === 'google_oauth_failed'
      ? 'Google sign-in failed. Please check OAuth redirect settings.'
      : ''
  )
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)

  function getRedirectUrl(includeNext = true) {
    if (!includeNext) {
      return `${window.location.origin}/auth/callback`
    }

    const next = encodeURIComponent(nextPath)
    return `${window.location.origin}/auth/callback?next=${next}`
  }

  async function handleGoogleLogin() {
    setError('')
    setMessage('')

    const supabase = createBrowserSupabaseClient()
    const { error: authError } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })

    if (authError) {
      console.error(authError.message)
      setError('Google sign-in failed. Please check OAuth redirect settings.')
    }
  }

  async function handleMagicLink(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedEmail = email.trim()
    setError('')
    setMessage('')

    if (!trimmedEmail) {
      setError('Enter your email to continue with a magic link.')
      return
    }

    setSending(true)
    const supabase = createBrowserSupabaseClient()
    const { error: authError } = await supabase.auth.signInWithOtp({
      email: trimmedEmail,
      options: {
        emailRedirectTo: getRedirectUrl(),
      },
    })
    setSending(false)

    if (authError) {
      setError(authError.message)
      return
    }

    setMessage('Check your email for the AetherTrip magic link.')
  }

  return (
    <main className="min-h-screen bg-[linear-gradient(125deg,#f8fdff_0%,#ffffff_42%,#e8fbff_100%)] text-[#171b22]">
      <div className="mx-auto grid min-h-screen max-w-6xl items-center gap-12 px-6 py-10 lg:grid-cols-[1fr_440px]">
        <section className="hidden lg:block">
          <Link href="/" className="mb-14 inline-flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#21c8ee] text-white">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} viewBox="0 0 24 24" aria-hidden>
                <path d="M12 3 5.5 5.7v5.8c0 4.1 2.7 7.8 6.5 9.1 3.8-1.3 6.5-5 6.5-9.1V5.7L12 3Z" />
                <path d="m9.4 12.1 1.7 1.7 3.7-4.1" />
              </svg>
            </span>
            <span className="text-2xl font-black tracking-[-0.04em] text-[#21c8ee]">AetherTrip</span>
          </Link>
          <h1 className="max-w-[620px] text-[54px] font-black leading-[0.98] tracking-[-0.045em]">
            Welcome back to AetherTrip
          </h1>
          <p className="mt-7 max-w-[520px] text-lg font-medium leading-8 text-[#65707b]">
            Sign in to save and reopen verified itineraries.
          </p>
        </section>

        <section className="rounded-2xl border border-[#dcebf0] bg-white p-8 shadow-[0_28px_80px_rgba(20,58,75,0.12)]">
          <div className="mb-8">
            <Link href="/" className="mb-8 inline-flex items-center gap-2 lg:hidden">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#21c8ee] text-white">A</span>
              <span className="font-black text-[#21c8ee]">AetherTrip</span>
            </Link>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[#21c8ee]">Secure access</p>
            <h2 className="mt-3 text-3xl font-black tracking-[-0.04em]">Welcome back to AetherTrip</h2>
            <p className="mt-3 text-sm font-medium leading-6 text-[#65707b]">
              Sign in to save and reopen verified itineraries.
            </p>
          </div>

          <button
            type="button"
            onClick={handleGoogleLogin}
            className="flex h-12 w-full items-center justify-center gap-3 rounded-lg border border-[#d7e2e8] bg-white text-sm font-black text-[#171b22] transition hover:-translate-y-0.5 hover:border-[#21c8ee] hover:shadow-[0_14px_30px_rgba(22,39,53,0.08)]"
          >
            <GoogleIcon />
            Continue with Google
          </button>

          <div className="my-7 flex items-center gap-3">
            <span className="h-px flex-1 bg-[#dce5ea]" />
            <span className="text-[11px] font-black uppercase tracking-[0.18em] text-[#8a95a1]">or</span>
            <span className="h-px flex-1 bg-[#dce5ea]" />
          </div>

          <form onSubmit={handleMagicLink} className="space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-black text-[#252b34]">Email magic link</span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="h-12 w-full rounded-lg border border-[#d7e2e8] bg-white px-4 text-sm font-semibold outline-none transition focus:border-[#21c8ee] focus:ring-4 focus:ring-cyan-100"
                placeholder="you@example.com"
              />
            </label>

            {error ? <p className="rounded-lg bg-red-50 px-4 py-3 text-sm font-bold text-red-600">{error}</p> : null}
            {message ? <p className="rounded-lg bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700">{message}</p> : null}

            <button
              type="submit"
              disabled={sending}
              className="flex h-12 w-full items-center justify-center gap-3 rounded-lg bg-[#21c8ee] text-sm font-black text-white shadow-[0_16px_32px_rgba(33,200,238,0.28)] transition hover:-translate-y-0.5 hover:bg-[#15bde5] disabled:cursor-not-allowed disabled:opacity-70"
            >
              <MailIcon />
              {sending ? 'Sending magic link' : 'Continue with email magic link'}
            </button>
          </form>

          <button
            type="button"
            disabled
            className="mt-4 flex h-11 w-full items-center justify-center rounded-lg border border-dashed border-[#cfdbe2] text-sm font-black text-[#8a95a1]"
          >
            Continue with Apple - Coming soon
          </button>
        </section>
      </div>
    </main>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-white text-sm font-bold text-slate-600">Loading login...</div>}>
      <LoginForm />
    </Suspense>
  )
}
