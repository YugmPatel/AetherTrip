import Link from 'next/link'
import type { ReactNode } from 'react'

const linkedInUrl = process.env.NEXT_PUBLIC_LINKEDIN_URL?.trim()
const githubRepoUrl = process.env.NEXT_PUBLIC_GITHUB_REPO_URL?.trim()

function LogoMark() {
  return (
    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#21c8ee] text-white">
      <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} viewBox="0 0 24 24">
        <path d="M12 3 5.5 5.7v5.8c0 4.1 2.7 7.8 6.5 9.1 3.8-1.3 6.5-5 6.5-9.1V5.7L12 3Z" />
        <path d="m9.4 12.1 1.7 1.7 3.7-4.1" />
      </svg>
    </span>
  )
}

function ExternalFooterLink({ href, children }: { href?: string; children: ReactNode }) {
  if (!href) {
    return <span className="cursor-not-allowed text-[#9aa4af]">{children}</span>
  }

  return (
    <a href={href} target="_blank" rel="noreferrer noopener" className="transition hover:text-[#21c8ee]">
      {children}
    </a>
  )
}

export default function Footer() {
  return (
    <footer className="border-t border-[#dce5ea] bg-[#f7f9fb]">
      <div className="mx-auto grid max-w-[1180px] gap-9 px-5 py-12 sm:px-8 md:grid-cols-[1.35fr_1fr_1fr_1fr]">
        <div>
          <Link href="/" className="flex items-center gap-2.5">
            <LogoMark />
            <span className="text-lg font-black tracking-[-0.04em] text-[#21c8ee]">AetherTrip</span>
          </Link>
          <p className="mt-5 max-w-[280px] text-sm font-medium leading-6 text-[#65707b]">
            Accuracy-first travel planning engine. We don't just plan, we verify and repair.
          </p>
          <p className="mt-7 text-xs font-medium text-[#a0a7af]">
            &copy; 2026 AetherTrip. Verified itineraries.
          </p>
        </div>

        <div>
          <h3 className="mb-4 text-sm font-black text-[#171b22]">Product</h3>
          <ul className="space-y-3 text-sm font-medium text-[#65707b]">
            <li><Link href="/plan" className="transition hover:text-[#21c8ee]">Plan a Trip</Link></li>
            <li><Link href="/how-it-works" className="transition hover:text-[#21c8ee]">How It Works</Link></li>
            <li><Link href="/verification-engine" className="transition hover:text-[#21c8ee]">Verification Engine</Link></li>
          </ul>
        </div>

        <div>
          <h3 className="mb-4 text-sm font-black text-[#171b22]">Company</h3>
          <ul className="space-y-3 text-sm font-medium text-[#65707b]">
            <li><Link href="/about" className="transition hover:text-[#21c8ee]">About</Link></li>
            <li><ExternalFooterLink href={linkedInUrl}>Contact</ExternalFooterLink></li>
            <li><ExternalFooterLink href={githubRepoUrl}>GitHub</ExternalFooterLink></li>
          </ul>
        </div>

        <div>
          <h3 className="mb-4 text-sm font-black text-[#171b22]">Legal</h3>
          <ul className="space-y-3 text-sm font-medium text-[#65707b]">
            <li><Link href="/privacy" className="transition hover:text-[#21c8ee]">Privacy Policy</Link></li>
            <li><Link href="/terms" className="transition hover:text-[#21c8ee]">Terms of Use</Link></li>
            <li><Link href="/accuracy-disclaimer" className="transition hover:text-[#21c8ee]">Accuracy Disclaimer</Link></li>
          </ul>
        </div>
      </div>
    </footer>
  )
}
