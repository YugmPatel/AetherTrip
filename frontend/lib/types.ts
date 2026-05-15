export type PipelineStatus = 'pending' | 'running' | 'completed' | 'failed'

export type SourceRef = {
  name?: string
  url?: string | null
  fetched_at?: string
  confidence?: number
}

export type PlaceCandidate = {
  id?: string
  name?: string
  category?: string
  address?: string | null
  latitude?: number
  longitude?: number
  rating?: number | null
  price_level?: string | null
  estimated_cost?: number | null
  opening_hours?: Record<string, unknown> | null
  dietary_tags?: string[]
  sources?: SourceRef[]
  source?: string
  source_provider?: string
  verification_status?: string
  opening_hours_status?: string | null
  opening_hours_text?: string | null
  scheduled_open_status?: string | null
  scheduled_time_window?: string | null
  weather_risk?: string | null
  weather_risk_level?: string | null
  weather_risk_reason?: string | null
  is_outdoor?: boolean | null
  validation_status?: string | null
  validation_issues?: ValidationIssue[]
  confidence?: number
  source_confidence?: number
  image_url?: string | null
  place_image_url?: string | null
  image_source?: string | null
  image_credit?: string | null
  image_confidence?: number | null
  description?: string | null
  phone?: string | null
  website?: string | null
}

export type TripConstraints = {
  origin?: string
  destination?: string
  duration_days?: number | null
  travelers?: number
  budget_per_person?: number | null
  diet?: string[]
  transport_mode?: string
  hard?: {
    origin?: string
    destination?: string
    start_date?: string | null
    end_date?: string | null
    duration_days?: number | null
    travelers?: number
    budget_per_person?: number | null
    currency?: string
    transport_mode?: string
    diet?: string[]
    must_visit?: string[]
    avoid?: string[]
    max_daily_walking_miles?: number | null
    safety_preference?: string | null
  }
  soft?: {
    pace?: string
    interests?: string[]
    trip_style?: string | null
    food_style?: string | null
    hotel_style?: string | null
    avoid_crowds?: boolean
    prefer_outdoor?: boolean
  }
}

export type ItineraryItem = {
  day?: number
  start_time?: string
  end_time?: string
  place_id?: string
  place_name?: string
  category?: string
  description?: string
  estimated_cost?: number
  travel_time_from_previous_minutes?: number | null
  source_confidence?: number
  notes?: string | null
  address?: string | null
  latitude?: number
  longitude?: number
  place?: PlaceCandidate | null
  image_url?: string | null
  image_source?: string | null
  image_credit?: string | null
  image_confidence?: number | null
  verification_status?: string | null
  opening_hours_status?: string | null
  opening_hours_text?: string | null
  scheduled_open_status?: string | null
  scheduled_time_window?: string | null
  weather_risk?: string | null
  weather_risk_level?: string | null
  weather_risk_reason?: string | null
  is_outdoor?: boolean | null
  validation_status?: string | null
  validation_issues?: ValidationIssue[]
}

export type DayPlan = {
  day?: number
  day_number?: number
  title?: string | null
  date?: string | null
  items?: ItineraryItem[]
  estimated_day_cost?: number
  estimated_walking_miles?: number | null
  weather_summary?: string | null
}

export type Itinerary = {
  destination?: string
  start_date?: string | null
  end_date?: string | null
  days?: DayPlan[]
  total_estimated_cost_per_person?: number
  total_estimated_travel_time_hours?: number | null
  notes?: string | null
  generation_method?: string | null
  warnings?: string[]
}

export type BudgetReport = {
  currency?: string
  travelers?: number
  lodging_base?: number
  intercity_transport?: number
  local_transport?: number
  food?: number
  attraction_tickets?: number
  lodging_taxes?: number
  lodging_fees?: number
  booking_fees?: number
  baggage_fees?: number
  seat_selection?: number
  parking?: number
  tolls?: number
  tips?: number
  currency_fees?: number
  emergency_buffer?: number
  total_base_cost?: number
  total_hidden_costs?: number
  total_per_person?: number
  total_for_group?: number
  total_estimated_cost?: number
  per_person_cost?: number
  budget_limit?: number | null
  base_costs?: Record<string, number>
  hidden_costs?: Record<string, number>
  user_budget_per_person?: number | null
  is_over_budget?: boolean
  budget_remaining_per_person?: number | null
  status?: 'unknown' | 'within_budget' | 'over_budget' | string
  warnings?: string[]
  breakdown_detail?: Record<string, { category?: string; amount?: number; notes?: string | null }>
  notes?: string | null
}

export type ValidationIssue = {
  type?: string
  severity?: 'info' | 'warning' | 'error' | 'critical'
  day?: number | null
  item_id?: string | null
  place_id?: string | null
  place_name?: string | null
  message?: string
  suggested_fix?: string | null
  evidence?: string | null
}

export type ValidationReport = {
  passed?: boolean
  issues?: ValidationIssue[]
  warnings?: ValidationIssue[]
  summary?: string | null
  checked_at?: string | null
}

export type FeasibilityScore = {
  overall_score?: number
  grade?: string
  status?: string
  breakdown?: Record<string, number>
  weights?: Record<string, number>
  generated_at?: string
  explanation?: string
  warnings?: string[]
  detailed_notes?: Record<string, string> | null
}

export type RepairHistoryItem = {
  report_index?: number
  issue_count?: number
  attempted?: boolean
  issue_type?: string
  fix_applied?: string
  before?: unknown
  after?: unknown
  reason?: string
  passed?: boolean
  [key: string]: unknown
}

export type TripResponse = {
  trip_id?: string
  user_input?: string
  parsed_request?: Record<string, unknown> | null
  constraints?: TripConstraints | null
  itinerary?: Itinerary | null
  budget_report?: BudgetReport | null
  validation_reports?: ValidationReport[]
  repair_history?: RepairHistoryItem[]
  feasibility_score?: FeasibilityScore | null
  place_candidates?: PlaceCandidate[]
  service_status?: Record<string, ServiceStatusEntry>
  data_sources?: Record<string, ServiceStatusEntry>
  why_this_trip_works?: string | null
  status?: string
  warnings?: string[]
  errors?: string[]
  created_at?: string | null
  completed_at?: string | null
  processing_time_seconds?: number | null
}

export type ServiceStatusEntry = {
  provider?: string
  status?: string
  destination?: string
  count?: number
  used_fallback?: boolean
  fallback_used?: boolean
  cache_hit?: boolean
  reason?: string
  warning?: string
  [key: string]: unknown
}

export type PipelineEvent = {
  stage: string
  label?: string
  status: PipelineStatus
  message?: string
  agent?: string
  service?: string
  timestamp?: string
  details?: Record<string, unknown>
  progress_percent?: number
  trip?: TripResponse
}

export type EnrichedItineraryItem = ItineraryItem & {
  place?: PlaceCandidate | null
  stableId: string
}
