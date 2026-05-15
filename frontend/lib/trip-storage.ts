import { createBrowserSupabaseClient } from '@/lib/supabase/client'
import { TripResponse } from '@/lib/types'
import { getDestination, normalizeTripResponse } from '@/lib/utils'

export type SavedTripRow = {
  id?: string
  user_id?: string
  trip_id: string
  destination: string | null
  title: string | null
  duration_days: number | null
  travelers: number | null
  budget_per_person: number | null
  feasibility_score: number | null
  feasibility_status: string | null
  trip_request: string | null
  trip_response: TripResponse
  created_at?: string | null
  updated_at?: string | null
}

type SaveTripResult =
  | { saved: true; trip: SavedTripRow }
  | { saved: false; reason: 'not_authenticated' | 'missing_trip_id' | 'table_missing' | 'error'; error?: string; code?: string }

type TripFetchResult =
  | { found: true; trip: TripResponse; row: SavedTripRow }
  | { found: false; reason: 'not_authenticated' | 'not_found' | 'table_missing' | 'error'; error?: string; code?: string }

type TripListResult =
  | { trips: SavedTripRow[]; reason?: undefined; error?: undefined }
  | { trips: SavedTripRow[]; reason: 'not_authenticated' | 'table_missing' | 'error'; error?: string; code?: string }

type TripCountResult =
  | { count: number; reason?: undefined; error?: undefined }
  | { count: null; reason: 'not_authenticated' | 'table_missing' | 'error'; error?: string; code?: string }

const SECRET_FIELD_PATTERN = /(api[_-]?key|service[_-]?role|secret|authorization|access[_-]?token|refresh[_-]?token|password)/i
const MISSING_TABLE_MESSAGE = 'Supabase trips table is missing. Run supabase/schema.sql in SQL Editor.'

type SupabaseErrorLike = {
  code?: string
  message?: string
}

function isTripsTableMissing(error?: SupabaseErrorLike | null) {
  const message = (error?.message || '').toLowerCase()
  return error?.code === 'PGRST205' || message.includes("could not find the table 'public.trips'") || message.includes('schema cache')
}

function formatSupabaseError(error?: SupabaseErrorLike | null) {
  if (isTripsTableMissing(error)) {
    return {
      reason: 'table_missing' as const,
      error: MISSING_TABLE_MESSAGE,
      code: error?.code,
    }
  }

  return {
    reason: 'error' as const,
    error: error?.message || 'Supabase request failed.',
    code: error?.code,
  }
}

export function getSupabaseHistoryErrorMessage(error?: string, reason?: string) {
  return reason === 'table_missing' ? MISSING_TABLE_MESSAGE : error || 'Unable to load saved trips.'
}

function sanitizeTripResponse(trip: TripResponse) {
  return JSON.parse(
    JSON.stringify(trip, (key, value) => {
      if (SECRET_FIELD_PATTERN.test(key)) {
        return '[redacted]'
      }

      return value
    })
  ) as TripResponse
}

export function mapTripResponseToSupabaseRow(
  tripResponse: TripResponse,
  originalPrompt: string | null,
  userId: string
): SavedTripRow & { user_id: string } {
  const normalized = normalizeTripResponse(tripResponse) || tripResponse
  const hard = normalized.constraints?.hard
  const destination = getDestination(normalized)
  const normalizedDestination = destination === 'Your Trip' ? null : destination
  const durationDays = hard?.duration_days ?? normalized.constraints?.duration_days ?? normalized.itinerary?.days?.length ?? null
  const travelers = hard?.travelers ?? normalized.constraints?.travelers ?? normalized.budget_report?.travelers ?? null
  const budgetPerPerson =
    hard?.budget_per_person ??
    normalized.constraints?.budget_per_person ??
    normalized.budget_report?.budget_limit ??
    normalized.budget_report?.user_budget_per_person ??
    null
  const feasibility = normalized.feasibility_score as (TripResponse['feasibility_score'] & { status?: string }) | null

  return {
    user_id: userId,
    trip_id: normalized.trip_id || '',
    destination: normalizedDestination,
    title: `Your ${normalizedDestination || 'Trip'} Itinerary`,
    duration_days: typeof durationDays === 'number' ? durationDays : null,
    travelers: typeof travelers === 'number' ? travelers : null,
    budget_per_person: typeof budgetPerPerson === 'number' ? budgetPerPerson : null,
    feasibility_score:
      typeof normalized.feasibility_score?.overall_score === 'number'
        ? Math.round(normalized.feasibility_score.overall_score)
        : null,
    feasibility_status: feasibility?.status || normalized.status || null,
    trip_request: originalPrompt || normalized.user_input || null,
    trip_response: sanitizeTripResponse(normalized),
    updated_at: new Date().toISOString(),
  }
}

export async function saveTripToSupabase(
  tripResponse: TripResponse,
  originalPrompt: string | null
): Promise<SaveTripResult> {
  const normalized = normalizeTripResponse(tripResponse) || tripResponse
  if (!normalized.trip_id) {
    return { saved: false, reason: 'missing_trip_id' }
  }

  const supabase = createBrowserSupabaseClient()
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser()

  if (userError || !user) {
    return { saved: false, reason: 'not_authenticated' }
  }

  const row = mapTripResponseToSupabaseRow(normalized, originalPrompt, user.id)
  const { data, error } = await supabase
    .from('trips')
    .upsert(row, { onConflict: 'user_id,trip_id' })
    .select('*')
    .single()

  if (error) {
    return { saved: false, ...formatSupabaseError(error) }
  }

  return { saved: true, trip: data as SavedTripRow }
}

export async function getTripFromSupabase(tripId: string): Promise<TripFetchResult> {
  const supabase = createBrowserSupabaseClient()
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser()

  if (userError || !user) {
    return { found: false, reason: 'not_authenticated' }
  }

  const { data, error } = await supabase.from('trips').select('*').eq('trip_id', tripId).maybeSingle()

  if (error) {
    return { found: false, ...formatSupabaseError(error) }
  }

  if (!data) {
    return { found: false, reason: 'not_found' }
  }

  return {
    found: true,
    row: data as SavedTripRow,
    trip: normalizeTripResponse((data as SavedTripRow).trip_response) || (data as SavedTripRow).trip_response,
  }
}

export async function listTripsFromSupabase(limit?: number): Promise<TripListResult> {
  const supabase = createBrowserSupabaseClient()
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser()

  if (userError || !user) {
    return { trips: [], reason: 'not_authenticated' }
  }

  let query = supabase.from('trips').select('*').order('created_at', { ascending: false })
  if (typeof limit === 'number') {
    query = query.limit(limit)
  }

  const { data, error } = await query

  if (error) {
    return { trips: [], ...formatSupabaseError(error) }
  }

  return { trips: (data || []) as SavedTripRow[] }
}

export async function countTripsFromSupabase(): Promise<TripCountResult> {
  const supabase = createBrowserSupabaseClient()
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser()

  if (userError || !user) {
    return { count: null, reason: 'not_authenticated' }
  }

  const { count, error } = await supabase.from('trips').select('id', { count: 'exact', head: true })

  if (error) {
    return { count: null, ...formatSupabaseError(error) }
  }

  return { count: count || 0 }
}

export async function deleteTripFromSupabase(tripId: string) {
  const supabase = createBrowserSupabaseClient()
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser()

  if (userError || !user) {
    return { deleted: false, reason: 'not_authenticated' as const }
  }

  const { error } = await supabase.from('trips').delete().eq('trip_id', tripId)

  if (error) {
    return { deleted: false, ...formatSupabaseError(error) }
  }

  return { deleted: true as const }
}
