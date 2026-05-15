import { TripResponse } from '@/lib/types'

type DataSourcesCardProps = {
  trip?: TripResponse | null
}

function statusLabel(value?: string) {
  if (!value) {
    return 'not reported'
  }

  return value.replace(/_/g, ' ')
}

export default function DataSourcesCard({ trip }: DataSourcesCardProps) {
  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  const sources = trip?.service_status || trip?.data_sources || {}
  const entries = Object.entries(sources)

  if (!entries.length) {
    return null
  }

  return (
    <details className="rounded-2xl border border-[#edf2f6] bg-white p-5 shadow-[0_20px_60px_rgba(22,39,53,0.08)]">
      <summary className="cursor-pointer text-sm font-black text-[#172033]">Data Sources</summary>
      <div className="mt-4 space-y-3">
        {entries.map(([name, source]) => (
          <div key={name} className="rounded-xl bg-[#f7fafc] p-3 text-xs font-semibold text-[#657184]">
            <div className="flex items-center justify-between gap-3">
              <span className="font-black capitalize text-[#172033]">{name.replace(/_/g, ' ')}</span>
              <span className="font-black uppercase text-[#21a9c9]">{statusLabel(source?.status)}</span>
            </div>
            <p className="mt-1">
              {source?.provider || 'provider unknown'}
              {typeof source?.count === 'number' ? ` | ${source.count} returned` : ''}
              {source?.used_fallback || source?.fallback_used ? ' | fallback used' : ''}
            </p>
            {source?.warning ? <p className="mt-1 text-amber-700">{source.warning}</p> : null}
          </div>
        ))}
      </div>
    </details>
  )
}
