import { confidencePercent, cn } from '@/lib/utils'

type SourceConfidenceProps = {
  value?: number | null
}

export default function SourceConfidence({ value }: SourceConfidenceProps) {
  const percent = confidencePercent(value)
  const low = typeof percent === 'number' && percent < 60
  const medium = typeof percent === 'number' && percent >= 60 && percent < 80

  return (
    <span
      className={cn(
        'rounded-full border px-2.5 py-1 text-[11px] font-black uppercase tracking-[0.04em]',
        low && 'border-amber-300 bg-amber-50 text-amber-700',
        medium && 'border-slate-300 bg-slate-50 text-slate-600',
        !low && !medium && 'border-emerald-300 bg-emerald-50 text-emerald-700'
      )}
    >
      {typeof percent === 'number' ? `${percent}% source confidence` : 'Source not verified'}
    </span>
  )
}
