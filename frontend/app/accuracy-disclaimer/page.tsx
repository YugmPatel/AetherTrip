import type { Metadata } from 'next'
import { CheckList, ContentCard, ContentGrid, NoteCard, StaticPageShell } from '@/components/StaticPage'

export const metadata: Metadata = {
  title: 'Accuracy Disclaimer - AetherTrip',
  description: 'How AetherTrip explains feasibility scores, validation limits, and changing travel data.',
}

export default function AccuracyDisclaimerPage() {
  return (
    <StaticPageShell
      eyebrow="Accuracy"
      title="Accuracy Disclaimer"
      subtitle="AetherTrip is accuracy-first, but travel data can be incomplete, stale, or change after a plan is generated."
      cta={{ href: '/plan', label: 'Back to Plan a Trip' }}
    >
      <ContentGrid>
        <ContentCard title="What AetherTrip checks">
          <p>
            AetherTrip checks route timing, opening hours when available, budget estimates, weather risk, source
            confidence, and constraint satisfaction.
          </p>
          <p>
            These checks are designed to surface common itinerary problems before users rely on the plan.
          </p>
        </ContentCard>

        <ContentCard title="Where accuracy can change">
          <CheckList
            items={[
              'Some data can be missing, stale, incomplete, or change after generation.',
              'Opening hours may be unknown or not returned by sources.',
              'Travel times can change due to traffic, transit delays, weather, closures, or local conditions.',
              'Budget estimates may miss changing taxes, fees, tips, surge prices, currency changes, or booking policies.',
            ]}
          />
        </ContentCard>
      </ContentGrid>

      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <ContentCard title="Feasibility Score means">
          <p>"This itinerary passed X% of our feasibility checks."</p>
        </ContentCard>

        <ContentCard title="Feasibility Score does not mean">
          <p>"X% chance the trip will succeed."</p>
        </ContentCard>
      </div>

      <div className="mt-5">
        <NoteCard>Users should verify critical details before booking or traveling.</NoteCard>
      </div>
    </StaticPageShell>
  )
}
