import { TripResponse, ValidationIssue } from '@/lib/types'
import { cleanDisplayMessage, cn } from '@/lib/utils'
import { getValidationWarningGroups, ValidationWarningGroup } from '@/lib/resultPage'

type ValidationWarningsProps = {
  trip?: TripResponse | null
}

function issueClass(issue: ValidationIssue) {
  const severity = issue.severity || 'warning'
  if (severity === 'critical' || severity === 'error') {
    return 'border-red-200 bg-red-50 text-red-700'
  }
  if (severity === 'info') {
    return 'border-slate-200 bg-slate-50 text-slate-700'
  }
  return 'border-amber-200 bg-amber-50 text-amber-800'
}

function IssueCard({ issue }: { issue: ValidationIssue }) {
  return (
    <div className={cn('rounded-xl border p-3 text-sm font-semibold leading-5', issueClass(issue))}>
      {cleanDisplayMessage(issue.message) || 'Validation issue returned without message.'}
      {issue.suggested_fix ? <p className="mt-1 text-xs opacity-80">Suggested fix: {issue.suggested_fix}</p> : null}
    </div>
  )
}

function GroupDetails({ group }: { group: ValidationWarningGroup }) {
  return (
    <details className="rounded-xl border border-amber-200 bg-amber-50 text-amber-900" open={group.key !== 'opening_hours'}>
      <summary className="cursor-pointer list-none p-3 text-sm font-black leading-5">
        <span className="block text-xs uppercase tracking-[0.12em] opacity-75">{group.title}</span>
        <span className="mt-1 block">{group.message}</span>
      </summary>
      <div className="space-y-2 border-t border-amber-200/70 px-3 pb-3 pt-2">
        {group.issues.map((issue, index) => (
          <div key={`${group.key}-${issue.type}-${index}`} className="rounded-lg bg-white/70 p-2 text-xs font-semibold leading-5">
            {cleanDisplayMessage(issue.message) || issue.place_name || issue.place_id || 'Validation issue returned without message.'}
            {issue.suggested_fix ? <p className="mt-1 opacity-80">Suggested fix: {issue.suggested_fix}</p> : null}
          </div>
        ))}
      </div>
    </details>
  )
}

export default function ValidationWarnings({ trip }: ValidationWarningsProps) {
  const { critical, groups } = getValidationWarningGroups(trip)
  const hasIssues = critical.length || groups.length

  return (
    <section className="rounded-2xl border border-[#edf2f6] bg-white p-6 shadow-[0_20px_60px_rgba(22,39,53,0.08)]">
      <h2 className="text-lg font-black tracking-[-0.03em]">Validation Warnings</h2>
      {!hasIssues ? (
        <p className="mt-4 rounded-xl bg-emerald-50 p-4 text-sm font-bold text-emerald-700">No critical issues found.</p>
      ) : (
        <div className="mt-4 space-y-4">
          {critical.length ? (
            <div>
              <p className="mb-2 text-xs font-black uppercase tracking-[0.12em] text-red-600">Critical</p>
              <div className="space-y-2">
                {critical.map((issue, index) => (
                  <IssueCard key={`${issue.type}-${index}`} issue={issue} />
                ))}
              </div>
            </div>
          ) : null}

          {groups.length ? (
            <div>
              <p className="mb-2 text-xs font-black uppercase tracking-[0.12em] text-[#8a98aa]">Grouped Warnings</p>
              <div className="space-y-2">
                {groups.map((group) => (
                  <GroupDetails key={group.key} group={group} />
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </section>
  )
}
