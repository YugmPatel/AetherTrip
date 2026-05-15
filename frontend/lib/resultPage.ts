import { BudgetReport, EnrichedItineraryItem, RepairHistoryItem, TripResponse, ValidationIssue } from '@/lib/types'
import { cleanDisplayMessage, formatCurrency, getIssues, getIssuesForItem, normalizeBreakdownKey } from '@/lib/utils'

export const UNKNOWN_VERIFY_TEXT = 'Unknown — verify manually'

type WhySectionTitle = 'Feasibility' | 'Budget Status' | 'Route Status' | 'Notes'

export type WhyTripSection = {
  title: WhySectionTitle
  items: string[]
}

export type PlaceValidationDetails = {
  openingHoursStatus: string
  scheduledOpenStatus: string
  scheduledTimeWindow: string
  weatherRisk: string
  weatherRiskLevel: string
  weatherRiskReason: string
  isOutdoor: boolean | null
  validationStatus: string
  openingHoursText: string
}

export type FormattedRepairHistoryItem = {
  action: string
  reason: string
  before: string
  after: string
  result: string
}

export type ValidationWarningGroup = {
  key: string
  title: string
  message: string
  issues: ValidationIssue[]
}

const whySectionTitles: WhySectionTitle[] = ['Feasibility', 'Budget Status', 'Route Status', 'Notes']

function isNumber(value: unknown): value is number {
  return typeof value === 'number' && !Number.isNaN(value)
}

function firstNumber(...values: unknown[]) {
  return values.find(isNumber)
}

function field(source: unknown, key: string) {
  return source && typeof source === 'object' ? (source as Record<string, unknown>)[key] : undefined
}

function textField(source: unknown, key: string) {
  const value = field(source, key)
  return typeof value === 'string' && value.trim() ? cleanMarkdownText(value) : ''
}

function hasSource(source: unknown) {
  const sources = field(source, 'sources')
  if (Array.isArray(sources) && sources.some((entry) => textField(entry, 'name') && textField(entry, 'name').toLowerCase() !== 'unknown')) {
    return true
  }

  return ['source', 'source_provider'].some((key) => {
    const value = textField(source, key).toLowerCase()
    return value && value !== 'unknown'
  })
}

function hasOpeningHours(value: unknown) {
  if (!value) {
    return false
  }
  if (typeof value === 'string') {
    return Boolean(value.trim())
  }
  if (typeof value === 'object') {
    return Object.keys(value).length > 0
  }
  return false
}

function booleanField(source: unknown, key: string) {
  const value = field(source, key)
  return typeof value === 'boolean' ? value : null
}

function issueType(issue: ValidationIssue) {
  return (issue.type || '').toLowerCase()
}

function issueText(issue?: ValidationIssue) {
  if (!issue) {
    return ''
  }
  return cleanMarkdownText(cleanDisplayMessage(issue.message) || issue.evidence || issue.suggested_fix || '')
}

function findIssue(issues: ValidationIssue[], needle: string) {
  return issues.find((issue) => issueType(issue).includes(needle))
}

function formatOpeningHours(hours: unknown) {
  if (!hasOpeningHours(hours)) {
    return UNKNOWN_VERIFY_TEXT
  }
  if (typeof hours === 'string') {
    return cleanMarkdownText(hours)
  }
  try {
    return JSON.stringify(hours, null, 2)
  } catch {
    return UNKNOWN_VERIFY_TEXT
  }
}
function displayStatus(value?: string | null) {
  if (!value) {
    return ''
  }

  return normalizeBreakdownKey(cleanMarkdownText(value))
}

function scheduledStatusLabel(status?: string | null) {
  const value = (status || '').toLowerCase()
  if (value === 'open_at_scheduled_time' || value.includes('open')) {
    return 'Open during scheduled visit.'
  }
  if (value === 'closed' || value.includes('closed')) {
    return 'Closed during scheduled visit.'
  }
  if (value === 'unknown' || value.includes('unknown')) {
    return UNKNOWN_VERIFY_TEXT
  }

  return status ? displayStatus(status) : UNKNOWN_VERIFY_TEXT
}

function weatherRiskLabel(level?: string | null) {
  const value = (level || '').toLowerCase()
  if (value.includes('high')) {
    return 'High'
  }
  if (value.includes('medium') || value.includes('moderate')) {
    return 'Medium'
  }
  if (value.includes('low')) {
    return 'Low'
  }

  return 'Unknown'
}

function weatherServiceSucceeded(trip?: TripResponse | null) {
  const status = trip?.service_status?.weather?.status || trip?.data_sources?.weather?.status
  return status === 'success'
}

export function cleanMarkdownText(value?: string | null) {
  if (!value) {
    return ''
  }

  return value
    .split(/\r?\n/)
    .map((line) =>
      line
        .replace(/^```.*$/, '')
        .replace(/^#{1,6}\s*/, '')
        .replace(/^>\s*/, '')
        .replace(/^\s*[-*+]\s+/, '')
        .replace(/^\s*\d+[.)]\s+/, '')
        .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/`([^`]*)`/g, '$1')
        .replace(/\*\*([^*]+)\*\*/g, '$1')
        .replace(/__([^_]+)__/g, '$1')
        .replace(/\*([^*]+)\*/g, '$1')
        .replace(/_([^_]+)_/g, '$1')
        .replace(/\s+/g, ' ')
        .trim()
    )
    .filter((line) => line && !/^[-*_]{3,}$/.test(line))
    .join('\n')
}

export function getCanonicalBudgetStatus(budget?: BudgetReport | null) {
  const perPerson = firstNumber(budget?.per_person_cost, budget?.total_per_person)
  const limit = firstNumber(budget?.budget_limit, budget?.user_budget_per_person)
  const costExceedsLimit = isNumber(perPerson) && isNumber(limit) && perPerson > limit
  const isOverBudget = Boolean(costExceedsLimit || budget?.is_over_budget === true)
  const status = isOverBudget ? 'over_budget' : isNumber(limit) ? 'within_budget' : 'unknown'

  return {
    status,
    isOverBudget,
    label: status === 'over_budget' ? 'Over budget' : status === 'within_budget' ? 'Within budget' : 'Budget unknown',
    perPerson,
    limit,
    remaining: isNumber(perPerson) && isNumber(limit) ? limit - perPerson : budget?.budget_remaining_per_person,
  }
}
export function describeBudgetStatus(budget?: BudgetReport | null) {
  const status = getCanonicalBudgetStatus(budget)
  const currency = budget?.currency || 'USD'

  if (status.status === 'over_budget') {
    if (isNumber(status.perPerson) && isNumber(status.limit)) {
      return `Estimated ${formatCurrency(status.perPerson, currency)} per person exceeds the ${formatCurrency(status.limit, currency)} limit.`
    }
    return 'Budget report is marked over budget.'
  }

  if (status.status === 'within_budget') {
    if (isNumber(status.perPerson) && isNumber(status.limit)) {
      return `Estimated ${formatCurrency(status.perPerson, currency)} per person is within the ${formatCurrency(status.limit, currency)} limit.`
    }
    return 'Budget report is within the stated limit.'
  }

  return UNKNOWN_VERIFY_TEXT
}

function sectionFromLine(line: string) {
  const match = line.match(/^(Feasibility|Budget Status|Route Status|Notes)\s*:?\s*(.*)$/i)
  if (!match) {
    return null
  }

  const title = whySectionTitles.find((candidate) => candidate.toLowerCase() === match[1].toLowerCase())
  return title ? { title, content: match[2].trim() } : null
}

function addSectionLine(sections: Record<WhySectionTitle, string[]>, title: WhySectionTitle, line?: string | null) {
  const cleaned = cleanMarkdownText(line)
  if (cleaned && !sections[title].includes(cleaned)) {
    sections[title].push(cleaned)
  }
}

export function getWhyTripTitle(trip?: TripResponse | null) {
  const score = trip?.feasibility_score?.overall_score
  return isNumber(score) && score < 70 ? 'Why This Trip Needs Review' : 'Why This Trip Works'
}

export function buildWhyTripSections(trip?: TripResponse | null): WhyTripSection[] {
  const sections: Record<WhySectionTitle, string[]> = {
    Feasibility: [],
    'Budget Status': [],
    'Route Status': [],
    Notes: [],
  }

  const score = trip?.feasibility_score
  if (isNumber(score?.overall_score)) {
    addSectionLine(sections, 'Feasibility', `Score ${score.overall_score}/100${score?.grade ? ` (${score.grade})` : ''}.`)
  } else {
    addSectionLine(sections, 'Feasibility', 'Feasibility score was not returned.')
  }

  addSectionLine(sections, 'Budget Status', describeBudgetStatus(trip?.budget_report))

  const issues = getIssues(trip)
  const routeIssues = issues.filter((issue) => issueType(issue).includes('travel_time') || issueType(issue).includes('route'))
  if (routeIssues.length) {
    routeIssues.forEach((issue) => addSectionLine(sections, 'Route Status', issueText(issue)))
  } else if (trip?.service_status?.routing?.status === 'success' || trip?.data_sources?.routing?.status === 'success') {
    addSectionLine(sections, 'Route Status', 'Route timing passed validation with the returned routing data.')
  } else {
    addSectionLine(sections, 'Route Status', UNKNOWN_VERIFY_TEXT)
  }

  const rawExplanation = trip?.why_this_trip_works || score?.explanation || ''
  let currentSection: WhySectionTitle = 'Notes'
  cleanMarkdownText(rawExplanation)
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line) => {
      const parsed = sectionFromLine(line)
      if (parsed) {
        currentSection = parsed.title
        addSectionLine(sections, parsed.title, parsed.content)
        return
      }
      addSectionLine(sections, currentSection, line)
    })

  if (!sections.Notes.length) {
    addSectionLine(
      sections,
      'Notes',
      issues.length
        ? 'Review validation warnings before booking.'
        : 'No additional backend notes were returned.'
    )
  }

  return whySectionTitles.map((title) => ({ title, items: sections[title] }))
}

export function getPlaceDetailValidation(item: EnrichedItineraryItem, trip?: TripResponse | null): PlaceValidationDetails {
  const place = item.place
  const issues = getIssuesForItem(trip, item)
  const unknownHoursIssue = findIssue(issues, 'unknown_opening_hours')
  const closedIssue = findIssue(issues, 'place_closed')
  const conflictIssue = findIssue(issues, 'opening_hours_conflict')
  const weatherIssue = findIssue(issues, 'weather_risk')
  const openingHours = place?.opening_hours
  const explicitOpeningText = textField(item, 'opening_hours_text') || textField(place, 'opening_hours_text')
  const hoursAvailable = hasOpeningHours(openingHours) || Boolean(explicitOpeningText)
  const sourceAvailable = hasSource(place)
  const hoursUnknown = Boolean(unknownHoursIssue || !hoursAvailable || !sourceAvailable)
  const explicitOpeningStatus = textField(item, 'opening_hours_status') || textField(place, 'opening_hours_status')
  const explicitScheduledStatus = textField(item, 'scheduled_open_status') || textField(place, 'scheduled_open_status')
  const explicitScheduledWindow = textField(item, 'scheduled_time_window') || textField(place, 'scheduled_time_window')
  const explicitWeatherRisk = textField(item, 'weather_risk') || textField(place, 'weather_risk')
  const explicitWeatherLevel = textField(item, 'weather_risk_level') || textField(place, 'weather_risk_level') || explicitWeatherRisk
  const explicitWeatherReason = textField(item, 'weather_risk_reason') || textField(place, 'weather_risk_reason')
  const isOutdoor = booleanField(item, 'is_outdoor') ?? booleanField(place, 'is_outdoor')
  const validationStatus = textField(item, 'validation_status') || textField(place, 'validation_status') || (issues.length ? 'Needs review' : 'No item-specific issues returned')

  const openingHoursStatus = hoursUnknown
      ? UNKNOWN_VERIFY_TEXT
      : displayStatus(explicitOpeningStatus) || (closedIssue || conflictIssue ? 'Needs review' : 'Opening-hour evidence returned from source')

  const scheduledOpenStatus = hoursUnknown && !explicitScheduledStatus
      ? UNKNOWN_VERIFY_TEXT
      : scheduledStatusLabel(explicitScheduledStatus || (closedIssue
      ? issueText(closedIssue) || 'Closed at scheduled time'
      : conflictIssue
      ? issueText(conflictIssue) || 'Opening-hours conflict'
      : 'open_at_scheduled_time'))

  const weatherRisk = displayStatus(explicitWeatherRisk) || (
    weatherIssue
      ? issueText(weatherIssue) || 'Weather risk reported'
      : weatherServiceSucceeded(trip)
      ? 'No weather risk returned'
      : 'Unknown or not outdoor-specific.'
  )

  return {
    openingHoursStatus,
    scheduledOpenStatus,
    scheduledTimeWindow: explicitScheduledWindow || 'Scheduled time window not returned.',
    weatherRisk,
    weatherRiskLevel: weatherRiskLabel(explicitWeatherLevel || (weatherIssue ? issueText(weatherIssue) : null)),
    weatherRiskReason: explicitWeatherReason || (weatherIssue ? issueText(weatherIssue) : '') || (isOutdoor ? weatherRisk : 'Unknown or not outdoor-specific.'),
    isOutdoor,
    validationStatus,
    openingHoursText: explicitOpeningText || formatOpeningHours(openingHours),
  }
}

function formatActionLabel(value: string) {
  const text = cleanMarkdownText(value)
  return text.includes('_') ? normalizeBreakdownKey(text) : text
}

export function formatRepairValue(value: unknown, depth = 0): string {
  if (value === null || typeof value === 'undefined' || value === '') {
    return ''
  }
  if (typeof value === 'string') {
    return cleanMarkdownText(cleanDisplayMessage(value))
  }
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  if (Array.isArray(value)) {
    return value.map((entry) => formatRepairValue(entry, depth + 1)).filter(Boolean).join(', ')
  }
  if (typeof value === 'object') {
    if (depth > 2) {
      return JSON.stringify(value)
    }

    return Object.entries(value)
      .map(([key, entry]) => {
        const formatted = formatRepairValue(entry, depth + 1)
        return formatted ? `${normalizeBreakdownKey(key)}: ${formatted}` : ''
      })
      .filter(Boolean)
      .join('; ')
  }

  return String(value)
}

export function formatRepairHistoryItem(repair: RepairHistoryItem, index = 0): FormattedRepairHistoryItem {
  const changed = repair.changed === true || repair.attempted === true || Boolean(repair.fix_applied || repair.action)
  const actionSource = repair.fix_applied || repair.action || repair.type || repair.issue_type || `Repair ${index + 1}`
  const resultSource = repair.result || (
    typeof repair.passed === 'boolean'
      ? repair.passed ? 'Passed validation' : 'Still needs review'
      : changed ? 'Repair applied' : 'No repair applied'
  )

  return {
    action: changed ? formatActionLabel(String(actionSource)) : 'No repair applied',
    reason: formatRepairValue(repair.reason || repair.why || repair.suggested_fix) || 'No reason returned.',
    before: formatRepairValue(repair.before),
    after: formatRepairValue(repair.after),
    result: formatRepairValue(resultSource) || 'No repair applied',
  }
}

function groupUnknownOpeningWarnings(warnings: ValidationIssue[]) {
  const unknownOpening = warnings.filter((issue) => issueType(issue).includes('unknown_opening_hours'))
  const others = warnings.filter((issue) => !issueType(issue).includes('unknown_opening_hours'))

  if (unknownOpening.length <= 1) {
    return [...unknownOpening, ...others]
  }

  const placeIds = unknownOpening.map((issue) => issue.place_id).filter(Boolean)
  const count = placeIds.length ? new Set(placeIds).size : unknownOpening.length
  return [
    {
      type: 'unknown_opening_hours_grouped',
      severity: 'warning',
      message: `${count} ${count === 1 ? 'place has' : 'places have'} unknown opening hours.`,
      suggested_fix: 'Verify opening hours manually.',
    } satisfies ValidationIssue,
    ...others,
  ]
}

export function getGroupedValidationIssues(trip?: TripResponse | null) {
  const issues = getIssues(trip)
  const critical = issues.filter((issue) => ['critical', 'error'].includes(issue.severity || 'warning'))
  const warnings = issues.filter((issue) => (issue.severity || 'warning') === 'warning')
  const info = issues.filter((issue) => (issue.severity || 'warning') === 'info')

  return {
    critical,
    warning: groupUnknownOpeningWarnings(warnings),
    info,
  }
}

function issuePlaceLabel(issue: ValidationIssue, index: number) {
  if (issue.place_name) {
    return issue.place_name
  }
  if (issue.place_id) {
    return issue.place_id
  }

  const message = cleanDisplayMessage(issue.message)
  const match = message.match(/^(.+?)\s+(?:has|does|is|was)\s+/i)
  return cleanMarkdownText(match?.[1]) || `Issue ${index + 1}`
}

function warningCategory(issue: ValidationIssue) {
  const text = `${issue.type || ''} ${issue.message || ''} ${issue.evidence || ''}`.toLowerCase()

  if (text.includes('opening') || text.includes('hours') || text.includes('closed')) {
    return 'opening_hours'
  }
  if (text.includes('budget') || text.includes('cost') || text.includes('price')) {
    return 'budget'
  }
  if (text.includes('route') || text.includes('travel_time') || text.includes('travel time') || text.includes('transit')) {
    return 'route'
  }
  if (text.includes('weather') || text.includes('rain') || text.includes('wind') || text.includes('heat')) {
    return 'weather'
  }
  if (text.includes('confidence') || text.includes('source') || text.includes('verified')) {
    return 'source_confidence'
  }

  return 'other'
}

function buildWarningGroup(key: string, issues: ValidationIssue[]): ValidationWarningGroup {
  if (key === 'opening_hours') {
    const labels = issues.map(issuePlaceLabel)
    const count = new Set(labels).size || issues.length
    return {
      key,
      title: 'Unknown Opening Hours',
      message: `${count} ${count === 1 ? 'place has' : 'places have'} unknown opening hours.`,
      issues,
    }
  }

  const titleByKey: Record<string, string> = {
    budget: 'Budget',
    route: 'Route',
    weather: 'Weather',
    source_confidence: 'Source Confidence',
    other: 'Other Warnings',
  }

  const title = titleByKey[key] || 'Other Warnings'
  return {
    key,
    title,
    message: `${issues.length} ${issues.length === 1 ? 'warning' : 'warnings'} grouped under ${title}.`,
    issues,
  }
}

export function getValidationWarningGroups(trip?: TripResponse | null) {
  const issues = getIssues(trip)
  const critical = issues.filter((issue) => ['critical', 'error'].includes(issue.severity || 'warning'))
  const groupable = issues.filter((issue) => !['critical', 'error'].includes(issue.severity || 'warning'))
  const buckets = groupable.reduce<Record<string, ValidationIssue[]>>((current, issue) => {
    const key = warningCategory(issue)
    current[key] = [...(current[key] || []), issue]
    return current
  }, {})

  const orderedKeys = ['opening_hours', 'budget', 'route', 'weather', 'source_confidence', 'other']
  return {
    critical,
    groups: orderedKeys
      .map((key) => (buckets[key]?.length ? buildWarningGroup(key, buckets[key]) : null))
      .filter((group): group is ValidationWarningGroup => Boolean(group)),
  }
}
