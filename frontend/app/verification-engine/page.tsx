import type { Metadata } from 'next'
import { CheckList, ContentCard, ContentGrid, NoteCard, StaticPageShell } from '@/components/StaticPage'

export const metadata: Metadata = {
  title: 'Verification Engine - AetherTrip',
  description: 'The validation layers AetherTrip uses to check itinerary feasibility at generation time.',
}

const engineLayers = [
  'Hard Constraint Satisfaction Engine',
  'Real-Time Grounded Verification Layer',
  'Spatial + Temporal Route Validator',
  'Budget Accuracy Engine + Hidden Cost Detector',
  'Auto-Repair Optimizer',
  'Feasibility Score + Confidence Score',
  'Explainable "Why This Trip Works" Report',
]

export default function VerificationEnginePage() {
  return (
    <StaticPageShell
      eyebrow="Validation System"
      title="The AetherTrip Verification Engine"
      subtitle="AetherTrip checks whether the itinerary passed feasibility checks using available data at generation time."
    >
      <ContentGrid>
        <ContentCard title="Validation Layers">
          <CheckList items={engineLayers} />
        </ContentCard>

        <ContentCard title="What The Score Means">
          <p>
            The feasibility score is an audit of route timing, place confidence, opening-hours availability, budget
            fit, weather risk, and constraint satisfaction.
          </p>
          <p>
            It describes what passed validation checks during generation, not what will remain unchanged after the plan
            is created.
          </p>
        </ContentCard>
      </ContentGrid>

      <div className="mt-5">
        <NoteCard>
          Opening hours, prices, weather, transit, and venue availability can change after generation. Users should
          verify critical details before booking or traveling.
        </NoteCard>
      </div>
    </StaticPageShell>
  )
}
