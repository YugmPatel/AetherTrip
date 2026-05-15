'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function LegacyNewTripRedirect() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/plan')
  }, [router])

  return (
    <main className="flex min-h-screen items-center justify-center bg-white text-sm font-bold text-slate-600">
      Opening the verified planner...
    </main>
  )
}
