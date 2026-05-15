import type { Metadata } from 'next'
import { CheckList, ContentCard, ContentGrid, NoteCard, StaticPageShell } from '@/components/StaticPage'

export const metadata: Metadata = {
  title: 'About AetherTrip - AetherTrip',
  description: 'About AetherTrip, an accuracy-first AI travel planner for realistic itineraries.',
}

export default function AboutPage() {
  return (
    <StaticPageShell
      eyebrow="About"
      title="About AetherTrip"
      subtitle="AetherTrip is built around one simple idea: AI travel plans should be checked before they are trusted."
    >
      <ContentGrid>
        <ContentCard title="Accuracy-first planning">
          <p>
            AetherTrip is an accuracy-first AI travel planner built to solve a real problem: AI itineraries often sound
            good but fail in the real world.
          </p>
          <p>
            AetherTrip combines AI planning with real APIs, deterministic validators, repair logic, and feasibility
            scoring so users can see whether a plan is actually usable.
          </p>
        </ContentCard>

        <ContentCard title="What guides the product">
          <CheckList
            items={[
              'Built for realistic travel planning',
              'Designed for transparency',
              'MVP/private beta disclaimer: features, sources, and validation coverage are still evolving.',
              "We don't just generate. We verify, repair, and explain.",
            ]}
          />
        </ContentCard>
      </ContentGrid>

      <div className="mt-5">
        <NoteCard>
          AetherTrip is currently an MVP and private beta experience. Validation can reduce common itinerary failures,
          but users should still confirm critical travel details before booking or traveling.
        </NoteCard>
      </div>
    </StaticPageShell>
  )
}
