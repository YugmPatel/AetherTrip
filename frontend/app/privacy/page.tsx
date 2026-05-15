import type { Metadata } from 'next'
import { CheckList, ContentCard, ContentGrid, NoteCard, StaticPageShell } from '@/components/StaticPage'

export const metadata: Metadata = {
  title: 'Privacy Policy - AetherTrip',
  description: 'MVP privacy policy for AetherTrip account, trip, and app operation data.',
}

const linkedInUrl = process.env.NEXT_PUBLIC_LINKEDIN_URL?.trim()

export default function PrivacyPage() {
  return (
    <StaticPageShell
      eyebrow="Legal"
      title="Privacy Policy"
      subtitle="This page explains the MVP data practices for AetherTrip accounts, prompts, generated itineraries, and saved trip history."
    >
      <ContentGrid>
        <ContentCard title="What we collect">
          <CheckList
            items={[
              'Account email, name, and avatar from the login provider',
              'Trip prompts and generated itineraries',
              'Saved trip history',
              'Basic technical data required for app operation',
            ]}
          />
        </ContentCard>

        <ContentCard title="How we use it">
          <CheckList
            items={[
              'Generate trips',
              'Save history',
              'Improve reliability',
              'Debug errors',
            ]}
          />
        </ContentCard>

        <ContentCard title="What we do not do">
          <CheckList
            items={[
              'Do not sell user data',
              'Do not expose private trips publicly',
              'Do not store backend API keys in trip records',
            ]}
          />
        </ContentCard>

        <ContentCard title="Third-party services">
          <CheckList
            items={[
              'Supabase for auth/history',
              'OpenRouter/Ollama for LLM planning',
              'Geoapify for places/geocoding/map tiles',
              'OpenRouteService for routing',
              'Open-Meteo for weather',
              'Wikidata/Wikipedia for knowledge enrichment',
            ]}
          />
        </ContentCard>
      </ContentGrid>

      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <ContentCard title="Contact">
          {linkedInUrl ? (
            <a href={linkedInUrl} target="_blank" rel="noreferrer noopener" className="font-black text-[#12add1]">
              Contact AetherTrip on LinkedIn
            </a>
          ) : (
            <span className="text-[#8994a1]">Contact link is not configured.</span>
          )}
        </ContentCard>

        <NoteCard>
          This is MVP copy, not legal advice. Replace with attorney-reviewed policy before public launch.
        </NoteCard>
      </div>
    </StaticPageShell>
  )
}
