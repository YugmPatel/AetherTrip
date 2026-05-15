'use client'

import { cn } from '@/lib/utils'

type PlaceImagePlaceholderProps = {
  category?: string | null
  className?: string
}

type PlaceholderMeta = {
  label: string
  glyph: string
  className: string
}

function getPlaceholderMeta(category?: string | null): PlaceholderMeta {
  const value = (category || '').toLowerCase()

  if (value.includes('museum') || value.includes('gallery')) {
    return { label: 'Museum', glyph: 'M', className: 'from-indigo-50 via-slate-50 to-cyan-50 text-indigo-700' }
  }
  if (value.includes('restaurant') || value.includes('food') || value.includes('cafe') || value.includes('market')) {
    return { label: 'Food', glyph: 'F', className: 'from-amber-50 via-orange-50 to-rose-50 text-amber-800' }
  }
  if (value.includes('park') || value.includes('nature') || value.includes('trail')) {
    return { label: 'Park', glyph: 'P', className: 'from-emerald-50 via-teal-50 to-cyan-50 text-emerald-800' }
  }
  if (value.includes('view')) {
    return { label: 'Viewpoint', glyph: 'V', className: 'from-sky-50 via-cyan-50 to-slate-50 text-sky-800' }
  }
  if (value.includes('attraction') || value.includes('landmark') || value.includes('monument')) {
    return { label: 'Attraction', glyph: 'A', className: 'from-cyan-50 via-slate-50 to-blue-50 text-cyan-800' }
  }

  return { label: 'Place', glyph: 'P', className: 'from-slate-50 via-cyan-50 to-slate-100 text-slate-700' }
}

export default function PlaceImagePlaceholder({ category, className }: PlaceImagePlaceholderProps) {
  const meta = getPlaceholderMeta(category)

  return (
    <div
      aria-label={`${meta.label} image placeholder`}
      className={cn('flex h-full w-full flex-col items-center justify-center bg-gradient-to-br', meta.className, className)}
    >
      <span className="flex h-10 w-10 items-center justify-center rounded-full border border-white/80 bg-white/65 text-base font-black shadow-sm">
        {meta.glyph}
      </span>
      <span className="mt-2 text-[10px] font-black uppercase tracking-[0.12em]">
        {meta.label}
      </span>
    </div>
  )
}
