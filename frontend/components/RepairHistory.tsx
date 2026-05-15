import { RepairHistoryItem } from '@/lib/types'
import { formatRepairHistoryItem } from '@/lib/resultPage'

type RepairHistoryProps = {
  repairs?: RepairHistoryItem[]
}

export default function RepairHistory({ repairs }: RepairHistoryProps) {
  return (
    <section className="rounded-2xl border border-[#edf2f6] bg-white p-6 shadow-[0_20px_60px_rgba(22,39,53,0.08)]">
      <h2 className="text-lg font-black tracking-[-0.03em]">Repair History</h2>
      {!repairs?.length ? (
        <p className="mt-4 rounded-xl bg-[#f7fafc] p-4 text-sm font-semibold text-[#657184]">No repair applied.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {repairs.map((repair, index) => {
            const formatted = formatRepairHistoryItem(repair, index)
            return (
              <div key={index} className="rounded-xl border border-cyan-200 bg-cyan-50 p-4 text-sm leading-6 text-[#255263]">
                <p className="font-black">Repair {index + 1}</p>
                <p className="font-semibold"><span className="font-black">Action:</span> {formatted.action}</p>
                <p className="font-semibold"><span className="font-black">Reason:</span> {formatted.reason}</p>
                {formatted.before ? (
                  <p className="mt-2 text-xs font-semibold opacity-80"><span className="font-black">Before:</span> {formatted.before}</p>
                ) : null}
                {formatted.after ? (
                  <p className="text-xs font-semibold opacity-80"><span className="font-black">After:</span> {formatted.after}</p>
                ) : null}
                <p className="mt-2 text-xs font-semibold opacity-80"><span className="font-black">Result:</span> {formatted.result}</p>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
