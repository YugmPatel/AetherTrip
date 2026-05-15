import type { Metadata } from 'next'
import { CheckList, ContentCard, NoteCard, StaticPageShell } from '@/components/StaticPage'

export const metadata: Metadata = {
  title: 'Terms of Use - AetherTrip',
  description: 'MVP terms of use for AetherTrip planning assistance and saved trip history.',
}

export default function TermsPage() {
  return (
    <StaticPageShell
      eyebrow="Legal"
      title="Terms of Use"
      subtitle="These MVP terms describe how AetherTrip should be used while the product is still evolving."
    >
      <ContentCard title="Use of AetherTrip">
        <CheckList
          items={[
            'AetherTrip provides planning assistance, not professional travel, legal, immigration, medical, emergency, or safety advice.',
            'Users are responsible for verifying bookings, prices, hours, entry rules, safety, and local conditions.',
            'Feasibility scores are validation audit scores, not guarantees.',
            'No booking/payment functionality is provided in this MVP.',
            'Users should not rely on AetherTrip for emergencies.',
            'Use of third-party services is subject to their terms.',
            'Account/history use requires login.',
          ]}
        />
      </ContentCard>

      <div className="mt-5">
        <NoteCard>This MVP terms page should be reviewed before public commercial launch.</NoteCard>
      </div>
    </StaticPageShell>
  )
}
