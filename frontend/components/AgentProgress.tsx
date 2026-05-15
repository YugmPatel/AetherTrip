'use client'

import { PipelineEvent } from '@/lib/types'
import { cn } from '@/lib/utils'
import PipelineStatus, { defaultPipelineStages, getCurrentEvent, getLatestEvents, getStageStatus } from '@/components/PipelineStatus'

type AgentProgressProps = {
  events: PipelineEvent[]
}

function StageIcon({ status, index }: { status: string; index: number }) {
  if (status === 'running') {
    return <span className="h-5 w-5 animate-spin rounded-full border-2 border-[#21c8ee] border-t-transparent" />
  }

  if (status === 'completed') {
    return (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} viewBox="0 0 24 24">
        <path d="m5 12 4 4 10-10" />
      </svg>
    )
  }

  if (status === 'failed') {
    return (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} viewBox="0 0 24 24">
        <path d="M12 8v5" />
        <path d="M12 17h.01" />
        <path d="M10.3 3.9 2.8 17a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
      </svg>
    )
  }

  return <span>{index + 1}</span>
}

export default function AgentProgress({ events }: AgentProgressProps) {
  const latest = getLatestEvents(events)
  const current = getCurrentEvent(events)

  return (
    <div className="min-h-screen bg-white text-[#172033]">
      <section className="mx-auto max-w-[1120px] px-5 py-16 sm:px-8">
        <div className="text-center">
          <div className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full bg-[#dff9fd] px-4 py-1.5 text-xs font-black uppercase tracking-[0.16em] text-[#15bee6]">
            <span className="h-2 w-2 animate-pulse rounded-full bg-[#21c8ee]" />
            Verification Engine Active
          </div>
          <h1 className="text-[44px] font-black leading-tight tracking-[-0.05em] md:text-[56px]">
            Verifying Your Itinerary
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg font-medium leading-8 text-[#708096]">
            Our AI engine is stress-testing your travel plan against real-world data, checking for conflicts, and
            optimizing your path.
          </p>
        </div>

        <div className="mt-10">
          <PipelineStatus events={events} />
        </div>

        <div className="mt-12 grid gap-8 lg:grid-cols-[1fr_360px]">
          <section className="rounded-2xl border border-[#edf2f6] bg-white shadow-[0_26px_80px_rgba(22,39,53,0.10)]">
            <div className="border-b border-[#edf2f6] px-7 py-7">
              <h2 className="text-2xl font-black tracking-[-0.035em]">Live Verification Log</h2>
              <p className="mt-1 text-sm font-medium text-[#708096]">Pipeline events update only when backend stages report progress.</p>
            </div>

            <div className="space-y-0 px-7 py-8">
              {defaultPipelineStages.map((stage, index) => {
                const event = latest.get(stage.stage)
                const status = getStageStatus(stage.stage, latest)
                const isActive = status === 'running'
                const isDone = status === 'completed'
                const isFailed = status === 'failed'

                return (
                  <div key={stage.stage} className="relative grid grid-cols-[54px_1fr] gap-5 pb-8 last:pb-0">
                    {index < defaultPipelineStages.length - 1 ? (
                      <span className="absolute left-[26px] top-12 h-[calc(100%-48px)] w-px bg-[#e5edf4]" />
                    ) : null}
                    <div
                      className={cn(
                        'relative z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-black',
                        isActive && 'border-[#21c8ee] bg-white text-[#21c8ee] shadow-[0_0_0_8px_rgba(33,200,238,0.10)]',
                        isDone && 'border-emerald-300 bg-emerald-50 text-emerald-600',
                        isFailed && 'border-red-300 bg-red-50 text-red-600',
                        !isActive && !isDone && !isFailed && 'border-[#d9e4ee] bg-white text-[#9aa8ba]'
                      )}
                    >
                      <StageIcon status={status} index={index} />
                    </div>

                    <div className={cn('pt-1', status === 'pending' && 'opacity-45')}>
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="text-lg font-black tracking-[-0.02em]">{event?.label || stage.label}</h3>
                        <span
                          className={cn(
                            'rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.08em]',
                            isActive && 'bg-cyan-50 text-[#0aaed3]',
                            isDone && 'bg-emerald-50 text-emerald-600',
                            isFailed && 'bg-red-50 text-red-600',
                            status === 'pending' && 'bg-slate-100 text-slate-500'
                          )}
                        >
                          {status}
                        </span>
                      </div>
                      <p className="mt-2 text-sm font-medium leading-6 text-[#718096]">
                        {event?.message || 'Waiting for backend event.'}
                      </p>
                      {(event?.agent || event?.service) && status !== 'pending' ? (
                        <div className="mt-3 rounded-xl bg-[#f7fafc] px-4 py-3 text-xs font-bold text-[#66758a]">
                          {event.agent || 'Agent'} {event.service ? `• ${event.service}` : ''}
                        </div>
                      ) : null}
                    </div>
                  </div>
                )
              })}
            </div>
          </section>

          <aside className="space-y-8">
            <section className="rounded-2xl border border-[#edf2f6] bg-white p-6 shadow-[0_20px_60px_rgba(22,39,53,0.09)]">
              <h2 className="flex items-center gap-2 text-xl font-black tracking-[-0.03em]">
                <span className="text-[#21c8ee]">↯</span>
                Engine Intelligence
              </h2>
              <div className="mt-5 space-y-5">
                <div className="flex gap-4">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#f0f5f9] text-[#516176]">✓</span>
                  <div>
                    <h3 className="text-sm font-black">Verified Reality</h3>
                    <p className="mt-1 text-xs font-semibold leading-5 text-[#6c7a8d]">
                      {current?.message || 'Waiting for the first backend event.'}
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#f0f5f9] text-[#516176]">↻</span>
                  <div>
                    <h3 className="text-sm font-black">Active Agent</h3>
                    <p className="mt-1 text-xs font-semibold leading-5 text-[#6c7a8d]">
                      {current?.agent || 'AetherTripGraph'} {current?.service ? `via ${current.service}` : ''}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-2xl border border-dashed border-[#d9e4ee] bg-[#fbfdff] p-8 text-center">
              <span className="mx-auto block h-9 w-9 animate-spin rounded-full border-4 border-[#b5c3d3] border-t-transparent" />
              <p className="mx-auto mt-5 max-w-[260px] text-sm font-semibold italic leading-6 text-[#8291a4]">
                This usually takes about 30-45 seconds. Please do not close your browser.
              </p>
            </section>
          </aside>
        </div>
      </section>
    </div>
  )
}
