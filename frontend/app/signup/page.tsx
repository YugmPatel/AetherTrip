'use client'

import { Suspense, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { getSafeNextPath } from '@/lib/auth'

function SignupRedirect() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const nextPath = getSafeNextPath(searchParams.get('next'))
  const loginPath = `/login?next=${encodeURIComponent(nextPath)}`

  useEffect(() => {
    router.replace(loginPath)
  }, [loginPath, router])

  return (
    <main className="flex min-h-screen items-center justify-center bg-white px-6 text-center text-[#171b22]">
      <div>
        <p className="text-xs font-black uppercase tracking-[0.18em] text-[#21c8ee]">Account access</p>
        <h1 className="mt-3 text-3xl font-black tracking-[-0.04em]">Registration now uses sign-in options</h1>
        <p className="mx-auto mt-3 max-w-md text-sm font-medium leading-6 text-[#65707b]">
          Google, Apple, or email magic link will create your profile automatically.
        </p>
        <Link
          href={loginPath}
          className="mt-7 inline-flex h-12 items-center justify-center rounded-lg bg-[#21c8ee] px-6 text-sm font-black text-white"
        >
          Continue to login
        </Link>
      </div>
    </main>
  )
}

export default function SignupPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-white text-sm font-bold text-slate-600">Loading account access...</div>}>
      <SignupRedirect />
    </Suspense>
  )
}
