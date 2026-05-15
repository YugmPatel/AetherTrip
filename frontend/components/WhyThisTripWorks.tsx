import { TripResponse } from '@/lib/types'
import { buildWhyTripSections, getWhyTripTitle } from '@/lib/resultPage'

type WhyThisTripWorksProps = {
  trip?: TripResponse | null
}

export default function WhyThisTripWorks({ trip }: WhyThisTripWorksProps) {
  const title = getWhyTripTitle(trip)

  if (!trip?.itinerary?.days?.length) {
    return (
      <section className="rounded-2xl bg-[#111b2e] p-6 text-white shadow-[0_20px_60px_rgba(17,27,46,0.22)]">
        <h2 className="text-lg font-black uppercase tracking-[0.05em] text-[#21c8ee]">{title}</h2>
        <p className="mt-5 text-sm font-semibold leading-6 text-slate-200">
          Feasibility details are unavailable because the itinerary was not generated.
        </p>
      </section>
    )
  }

  const sections = buildWhyTripSections(trip)

  return (
    <section className="rounded-2xl bg-[#111b2e] p-6 text-white shadow-[0_20px_60px_rgba(17,27,46,0.22)]">
      <h2 className="text-lg font-black uppercase tracking-[0.05em] text-[#21c8ee]">{title}</h2>
      <div className="mt-5 space-y-5">
        {sections.map((section) => (
          <div key={section.title}>
            <h3 className="text-xs font-black uppercase tracking-[0.12em] text-slate-400">{section.title}</h3>
            <div className="mt-2 space-y-2">
              {section.items.map((item, index) => (
                <p key={`${section.title}-${index}`} className="text-sm font-semibold leading-6 text-slate-200">
                  {item}
                </p>
              ))}
            </div>
          </div>
        ))}
      </div>
      <p className="mt-6 rounded-xl bg-white/6 p-3 text-xs font-semibold italic text-slate-400">
        Feasibility reflects fetched data at generation time. Always check local notices before booking.
      </p>
    </section>
  )
}
