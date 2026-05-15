import type { User } from '@supabase/supabase-js'
import { createBrowserSupabaseClient } from '@/lib/supabase/client'

export type Profile = {
  id: string
  full_name: string | null
  email: string | null
  avatar_url: string | null
  created_at?: string | null
  updated_at?: string | null
}

export function getProfileFields(user: User): Profile {
  const metadata = user.user_metadata || {}
  const fullName =
    typeof metadata.full_name === 'string'
      ? metadata.full_name
      : typeof metadata.name === 'string'
        ? metadata.name
        : null
  const avatarUrl =
    typeof metadata.avatar_url === 'string'
      ? metadata.avatar_url
      : typeof metadata.picture === 'string'
        ? metadata.picture
        : null

  return {
    id: user.id,
    full_name: fullName,
    email: user.email || null,
    avatar_url: avatarUrl,
  }
}

export async function upsertCurrentProfile(user: User) {
  const supabase = createBrowserSupabaseClient()
  const profile = getProfileFields(user)

  const { error } = await supabase.from('profiles').upsert(
    {
      ...profile,
      updated_at: new Date().toISOString(),
    },
    { onConflict: 'id' }
  )

  return { profile, error }
}
