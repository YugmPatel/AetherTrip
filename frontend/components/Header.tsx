'use client'

import Link from 'next/link'
import AuthMenu from '@/components/AuthMenu'
import { useAuthUser } from '@/lib/auth'

function ShieldIcon() {
  return (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} viewBox="0 0 24 24">
      <path d="M12 3 5.5 5.7v5.8c0 4.1 2.7 7.8 6.5 9.1 3.8-1.3 6.5-5 6.5-9.1V5.7L12 3Z" />
      <path d="m9.4 12.1 1.7 1.7 3.7-4.1" />
    </svg>
  )
}

function SmallIcon({ type }: { type: 'plus' | 'history' }) {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} viewBox="0 0 24 24">
      {type === 'plus' ? (
        <>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v8" />
          <path d="M8 12h8" />
        </>
      ) : (
        <>
          <path d="M3 12a9 9 0 1 0 3-6.7" />
          <path d="M3 4v5h5" />
          <path d="M12 7v5l3 2" />
        </>
      )}
    </svg>
  )
}

export default function Header() {
  const user = useAuthUser()

  return (
    <header className="sticky top-0 z-40 border-b border-[#dce5ea] bg-white/95 shadow-[0_1px_18px_rgba(14,33,48,0.05)] backdrop-blur">
      <div className="mx-auto flex h-[72px] max-w-[1280px] items-center justify-between px-5 sm:px-8">
        <div className="flex items-center gap-10">
          <Link href="/" className="flex items-center gap-3" aria-label="AetherTrip home">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#21c8ee] text-white shadow-[0_10px_24px_rgba(33,200,238,0.24)]">
              <ShieldIcon />
            </span>
            <span className="text-[23px] font-black tracking-[-0.045em] text-[#21c8ee]">AetherTrip</span>
          </Link>

          <nav className="hidden items-center gap-9 text-[15px] font-semibold md:flex">
            <Link href="/plan" className="flex items-center gap-2 text-[#14bfe8] transition hover:text-[#0aaed3]">
              <SmallIcon type="plus" />
              New Plan
            </Link>
            <Link href="/history" className="flex items-center gap-2 text-[#172033] transition hover:text-[#0aaed3]">
              <SmallIcon type="history" />
              History
            </Link>
          </nav>
        </div>

        <AuthMenu user={user} nextPath="/plan" />
      </div>
    </header>
  )
}
