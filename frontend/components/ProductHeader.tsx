'use client'

import Link from 'next/link'
import AuthMenu from '@/components/AuthMenu'
import { useAuthUser } from '@/lib/auth'

function HeaderIcon({ name }: { name: 'shield' | 'plus' | 'history' }) {
  const common = {
    className: name === 'shield' ? 'h-5 w-5' : 'h-4 w-4',
    fill: 'none',
    stroke: 'currentColor',
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    strokeWidth: 2,
    viewBox: '0 0 24 24',
    'aria-hidden': true,
  }

  if (name === 'plus') {
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8v8" />
        <path d="M8 12h8" />
      </svg>
    )
  }

  if (name === 'history') {
    return (
      <svg {...common}>
        <path d="M3 12a9 9 0 1 0 3-6.7" />
        <path d="M3 4v5h5" />
        <path d="M12 7v5l3 2" />
      </svg>
    )
  }

  return (
    <svg {...common}>
      <path d="M12 3 5.5 5.7v5.8c0 4.1 2.7 7.8 6.5 9.1 3.8-1.3 6.5-5 6.5-9.1V5.7L12 3Z" />
      <path d="m9.4 12.1 1.7 1.7 3.7-4.1" />
    </svg>
  )
}

export default function ProductHeader() {
  const user = useAuthUser()

  return (
    <header className="border-b border-[#dce5ea] bg-white">
      <div className="mx-auto flex h-[72px] max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-10">
          <Link href="/" className="flex items-center gap-3" aria-label="AetherTrip home">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#21c8ee] text-white shadow-[0_10px_24px_rgba(33,200,238,0.24)]">
              <HeaderIcon name="shield" />
            </span>
            <span className="text-[24px] font-black tracking-[-0.04em] text-[#21c8ee]">AetherTrip</span>
          </Link>

          <nav className="hidden items-center gap-10 text-[15px] font-semibold md:flex">
            <Link href="/plan" className="flex items-center gap-2 text-[#14bfe8] transition hover:text-[#0aaed3]">
              <HeaderIcon name="plus" />
              New Plan
            </Link>
            <Link href="/history" className="flex items-center gap-2 text-[#18212f] transition hover:text-[#0aaed3]">
              <HeaderIcon name="history" />
              History
            </Link>
          </nav>
        </div>

        <AuthMenu user={user} nextPath="/plan" />
      </div>
    </header>
  )
}
