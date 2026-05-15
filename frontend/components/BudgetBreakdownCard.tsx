import { BudgetReport } from '@/lib/types'
import { getCanonicalBudgetStatus } from '@/lib/resultPage'
import { formatCurrency } from '@/lib/utils'

type BudgetBreakdownCardProps = {
  budget?: BudgetReport | null
}

const baseKeys = ['lodging_base', 'intercity_transport', 'local_transport', 'food', 'attraction_tickets'] as const
const hiddenKeys = [
  'lodging_taxes',
  'lodging_fees',
  'booking_fees',
  'baggage_fees',
  'seat_selection',
  'parking',
  'tolls',
  'tips',
  'currency_fees',
  'emergency_buffer',
] as const

function label(key: string) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function numeric(value: unknown): value is number {
  return typeof value === 'number' && !Number.isNaN(value)
}

function budgetValue(budget: BudgetReport | null | undefined, key: string) {
  const direct = budget?.[key as keyof BudgetReport]
  if (numeric(direct)) {
    return direct
  }

  const base = budget?.base_costs?.[key]
  if (numeric(base)) {
    return base
  }

  const hidden = budget?.hidden_costs?.[key]
  if (numeric(hidden)) {
    return hidden
  }

  return undefined
}

function sumKnownValues(budget: BudgetReport | null | undefined, keys: readonly string[]) {
  const values = keys.map((key) => budgetValue(budget, key)).filter(numeric)
  return values.length ? values.reduce((sum, value) => sum + value, 0) : undefined
}

export default function BudgetBreakdownCard({ budget }: BudgetBreakdownCardProps) {
  const currency = budget?.currency || 'USD'
  const perPerson = budget?.per_person_cost ?? budget?.total_per_person
  const total = budget?.total_estimated_cost ?? budget?.total_for_group
  const budgetLimit = budget?.budget_limit ?? budget?.user_budget_per_person
  const hiddenTotal = budget?.total_hidden_costs ?? sumKnownValues(budget, hiddenKeys)
  const baseTotal = budget?.total_base_cost ?? sumKnownValues(budget, baseKeys)
  const status = getCanonicalBudgetStatus(budget)

  return (
    <section className="rounded-2xl border border-[#edf2f6] bg-white p-6 shadow-[0_20px_60px_rgba(22,39,53,0.08)]">
      <p className="text-xs font-black uppercase tracking-[0.12em] text-emerald-600">Estimated Budget</p>
      <div className="mt-3 flex items-end justify-between gap-4">
        <div>
          <p className="text-4xl font-black tracking-[-0.06em] text-[#172033]">
            {formatCurrency(perPerson, currency)}
          </p>
          <p className="mt-1 text-xs font-bold uppercase tracking-[0.08em] text-[#8a98aa]">Per person</p>
        </div>
        {status.status !== 'unknown' ? (
          <span className={status.isOverBudget ? 'text-sm font-black text-red-600' : 'text-sm font-black text-emerald-600'}>
            {status.label}
          </span>
        ) : (
          <span className="text-sm font-black text-[#8a98aa]">Budget unknown</span>
        )}
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-xl bg-[#f7fafc] p-3">
          <p className="text-xs font-black uppercase text-[#8a98aa]">Group Total</p>
          <p className="mt-1 font-black text-[#172033]">{formatCurrency(total, currency)}</p>
        </div>
        <div className="rounded-xl bg-[#f7fafc] p-3">
          <p className="text-xs font-black uppercase text-[#8a98aa]">Budget Limit</p>
          <p className="mt-1 font-black text-[#172033]">{formatCurrency(budgetLimit, currency)}</p>
        </div>
      </div>

      <div className="mt-6 space-y-2 text-sm">
        <div className="mb-2 flex justify-between gap-4 font-black text-[#172033]">
          <span>Base Costs</span>
          <span>{formatCurrency(baseTotal, currency)}</span>
        </div>
        {baseKeys.map((key) => (
          <div key={key} className="flex justify-between gap-4 text-[#5d6b7d]">
            <span>{label(key)}</span>
            <span className="font-bold text-[#172033]">{formatCurrency(budgetValue(budget, key), currency)}</span>
          </div>
        ))}
      </div>

      <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
        <div className="mb-3 flex items-center justify-between text-sm font-black text-amber-800">
          <span>Hidden Costs Forecast</span>
          <span>{formatCurrency(hiddenTotal, currency)}</span>
        </div>
        <div className="space-y-1.5 text-xs font-semibold text-amber-800/85">
          {hiddenKeys.map((key) => {
            const value = budgetValue(budget, key)
            if (!numeric(value) || value <= 0) {
              return null
            }

            return (
              <div key={key} className="flex justify-between">
                <span>{label(key)}</span>
                <span>{formatCurrency(value, currency)}</span>
              </div>
            )
          })}
          {!numeric(hiddenTotal) ? <p>Hidden cost details were not returned.</p> : null}
        </div>
      </div>

      {typeof budget?.budget_remaining_per_person === 'number' ? (
        <p className="mt-4 text-sm font-semibold text-[#657184]">
          Remaining buffer: {formatCurrency(budget.budget_remaining_per_person, currency)} per person.
        </p>
      ) : null}

      {(budget?.warnings || []).length ? (
        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs font-semibold text-amber-800">
          {budget?.warnings?.[0]}
        </div>
      ) : null}
    </section>
  )
}
