'use client'

import type { User } from '@supabase/supabase-js'
import { useEffect, useState } from 'react'
import { upsertCurrentProfile } from '@/lib/profile'
import { createBrowserSupabaseClient } from '@/lib/supabase/client'

export type AuthProvider = 'google' | 'apple' | 'email' | 'unknown'

export type AuthUser = {
  id: string
  name: string
  email: string
  avatarUrl: string | null
  provider: AuthProvider
  createdAt: string
}

export type AuthSession = {
  user: AuthUser | null
  hydrated: boolean
}

function getSafeName(name: string | null | undefined, email: string | null | undefined) {
  const trimmedName = name?.trim()
  if (trimmedName) {
    return trimmedName
  }

  const emailName = email?.split('@')[0]?.replace(/[._-]+/g, ' ').trim()
  return emailName ? emailName.replace(/\b\w/g, (char) => char.toUpperCase()) : 'Aether Traveler'
}

function getUserMetadataString(user: User, key: string) {
  const value = user.user_metadata?.[key]
  return typeof value === 'string' ? value : null
}

function getAuthProvider(user: User): AuthProvider {
  const provider = typeof user.app_metadata?.provider === 'string' ? user.app_metadata.provider : 'unknown'
  return provider === 'google' || provider === 'apple' || provider === 'email' ? provider : 'unknown'
}

export function mapSupabaseUser(user: User): AuthUser {
  const fullName = getUserMetadataString(user, 'full_name') || getUserMetadataString(user, 'name')
  const avatarUrl = getUserMetadataString(user, 'avatar_url') || getUserMetadataString(user, 'picture')

  return {
    id: user.id,
    name: getSafeName(fullName, user.email),
    email: user.email || '',
    avatarUrl,
    provider: getAuthProvider(user),
    createdAt: user.created_at,
  }
}

export function getUserInitials(user: Pick<AuthUser, 'name' | 'email'>) {
  const source = user.name.trim() || user.email.split('@')[0]?.replace(/[._-]+/g, ' ') || 'Aether Traveler'
  const initials = source
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')

  return initials || 'AT'
}

export function getLoginPath(nextPath = '/plan') {
  return `/login?next=${encodeURIComponent(nextPath)}`
}

export function getProtectedPath(_user: AuthUser | null, nextPath = '/plan') {
  return nextPath
}

export function getSafeNextPath(nextPath: string | null) {
  if (!nextPath || !nextPath.startsWith('/') || nextPath.startsWith('//')) {
    return '/plan'
  }

  return nextPath
}

export async function signOutAuth() {
  const supabase = createBrowserSupabaseClient()
  await supabase.auth.signOut()
}

export async function clearAuthUser() {
  await signOutAuth()
}

export function useAuthSession() {
  const [session, setSession] = useState<AuthSession>({
    user: null,
    hydrated: false,
  })

  useEffect(() => {
    const supabase = createBrowserSupabaseClient()
    let active = true

    const syncUser = async (user: User | null) => {
      if (!active) {
        return
      }

      setSession({
        user: user ? mapSupabaseUser(user) : null,
        hydrated: true,
      })

      if (user) {
        void upsertCurrentProfile(user)
      }
    }

    supabase.auth.getUser().then(({ data }) => {
      void syncUser(data.user)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, authSession) => {
      void syncUser(authSession?.user || null)
    })

    return () => {
      active = false
      subscription.unsubscribe()
    }
  }, [])

  return session
}

export function useAuthUser() {
  return useAuthSession().user
}
