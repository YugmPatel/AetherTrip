import type { Metadata } from 'next'
import { ContentCard, ContentGrid, StaticPageShell } from '@/components/StaticPage'

export const metadata: Metadata = {
  title: 'How AetherTrip Works - AetherTrip',
  description: 'How AetherTrip builds, validates, repairs, and explains AI travel itineraries.',
}

const steps = [
  {
    title: 'Understand your trip',
    body:
      'AetherTrip extracts destination, duration, dates, travelers, budget, diet, transport mode, pace, must-visit places, and hard constraints.',
  },
  {
    title: 'Fetch grounded data',
    body:
      'AetherTrip checks real data sources for places, geocoding, weather, routing, and knowledge enrichment.',
  },
  {
    title: 'Build a candidate itinerary',
    body: 'The AI proposes an itinerary using verified place candidates instead of inventing places.',
  },
  {
    title: 'Validate the plan',
    body:
      'AetherTrip checks opening hours, travel time, route feasibility, budget, hidden costs, weather risk, source confidence, and constraint satisfaction.',
  },
  {
    title: 'Repair problems',
    body:
      'If something is closed, too far, over budget, or low confidence, AetherTrip attempts to repair the plan or marks it as needs review.',
  },
  {
    title: 'Explain feasibility',
    body:
      'The feasibility score is an audit score showing how much of the itinerary passed validation checks at generation time. It is not a guarantee.',
  },
]

export default function HowItWorksPage() {
  return (
    <StaticPageShell
      eyebrow="Planning Workflow"
      title="How AetherTrip Works"
      subtitle="AetherTrip turns a natural-language trip idea into a grounded, checked itinerary with visible repairs and validation notes."
      cta={{ href: '/plan', label: 'Plan a verified trip' }}
    >
      <ContentGrid>
        {steps.map((step, index) => (
          <ContentCard key={step.title} eyebrow={`Step ${index + 1}`} title={step.title}>
            <p>{step.body}</p>
          </ContentCard>
        ))}
      </ContentGrid>
    </StaticPageShell>
  )
}
