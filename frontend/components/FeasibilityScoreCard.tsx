import { FeasibilityScore } from '@/lib/types'
import { formatPercent, normalizeBreakdownKey } from '@/lib/utils'

type FeasibilityScoreCardProps = {
  score?: FeasibilityScore | null
}

export default function FeasibilityScoreCard({ score }: FeasibilityScoreCardProps) {
  const overall = score?.overall_score
  const breakdown = score?.breakdown || {}
  const rows = Object.entries(breakdown)

  return (
    <section className="rounded-2xl border border-[#edf2f6] bg-white p-6 shadow-[0_20px_60px_rgba(22,39,53,0.08)]">
      <p className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.12em] text-emerald-600">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        Verification Status: {overall && overall >= 80 ? 'High' : 'Needs Review'}
      </p>
      <div className="flex items-end gap-2">
        <span className="text-5xl font-black tracking-[-0.07em] text-[#172033]">{typeof overall === 'number' ? overall : '--'}</span>
        <span className="mb-2 text-xl font-black text-[#91a0b3]">/100</span>
      </div>
      <p className="mt-3 text-sm font-bold leading-6 text-[#66758a]">
        {typeof overall === 'number'
          ? `This itinerary passed ${formatPercent(overall)} of our feasibility checks.`
          : 'Feasibility score was not returned by the backend.'}
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {rows.length ? (
          rows.map(([key, value]) => (
            <div key={key}>
              <div className="mb-1.5 flex items-center justify-between text-xs font-bold text-[#506176]">
                <span>{normalizeBreakdownKey(key)}</span>
                <span className="text-emerald-600">{formatPercent(value)}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-[#e8eef4]">
                <div className="h-full rounded-full bg-[#21c8ee]" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
              </div>
            </div>
          ))
        ) : (
          <p className="col-span-2 text-sm font-medium text-[#75859a]">No score breakdown was returned.</p>
        )}
      </div>

      <div className="mt-6 rounded-xl bg-[#f7fafc] p-4 text-sm font-semibold leading-6 text-[#657184]">
        Score reflects validation at generation time using fetched data and deterministic checks.
      </div>
    </section>
  )
}
