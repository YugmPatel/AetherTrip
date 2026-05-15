'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import UserAvatar from '@/components/UserAvatar'
import { AuthUser, getLoginPath, signOutAuth } from '@/lib/auth'

type AuthMenuProps = {
  user: AuthUser | null
  nextPath?: string
}

export default function AuthMenu({ user, nextPath = '/plan' }: AuthMenuProps) {
  const router = useRouter()
  const [open, setOpen] = useState(false)

  async function handleSignOut() {
    await signOutAuth()
    setOpen(false)
    router.replace('/')
    router.refresh()
  }

  if (!user) {
    return (
      <Link href={getLoginPath(nextPath)} className="text-sm font-bold text-[#172033] transition hover:text-[#21c8ee]">
        Login
      </Link>
    )
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex items-center gap-3 rounded-full px-2 py-1 text-left transition hover:bg-slate-50"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <span className="hidden max-w-[160px] text-right sm:block">
          <span className="block truncate text-xs font-medium text-[#657184]">{user.name}</span>
          <span className="block truncate text-[11px] font-bold text-[#21c8ee]">{user.email}</span>
        </span>
        <UserAvatar user={user} showStatus />
      </button>

      {open ? (
        <div
          role="menu"
          className="absolute right-0 top-12 z-50 w-48 overflow-hidden rounded-xl border border-[#dce5ea] bg-white py-2 shadow-[0_18px_45px_rgba(22,39,53,0.14)]"
        >
          <Link
            href="/profile"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="block px-4 py-2.5 text-sm font-bold text-[#172033] transition hover:bg-[#f5fbfd] hover:text-[#0aaed3]"
          >
            Profile
          </Link>
          <Link
            href="/history"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="block px-4 py-2.5 text-sm font-bold text-[#172033] transition hover:bg-[#f5fbfd] hover:text-[#0aaed3]"
          >
            History
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={handleSignOut}
            className="block w-full px-4 py-2.5 text-left text-sm font-bold text-red-600 transition hover:bg-red-50"
          >
            Sign out
          </button>
        </div>
      ) : null}
    </div>
  )
}
