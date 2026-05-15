import type { ReactNode } from 'react'
import Link from 'next/link'
import Footer from '@/components/Footer'
import Header from '@/components/Header'

type StaticPageShellProps = {
  eyebrow: string
  title: string
  subtitle?: string
  cta?: {
    href: string
    label: string
  }
  children: ReactNode
}

export function StaticPageShell({ eyebrow, title, subtitle, cta, children }: StaticPageShellProps) {
  return (
    <main className="min-h-screen bg-white text-[#172033]">
      <Header />
      <section className="border-b border-[#dce5ea] bg-[linear-gradient(110deg,#f1fdff_0%,#ffffff_44%,#f8fbff_100%)]">
        <div className="mx-auto max-w-[1040px] px-5 py-16 sm:px-8 md:py-20">
          <div className="mb-5 inline-flex items-center rounded-full bg-[#dff9fd] px-4 py-1.5 text-xs font-black uppercase tracking-[0.14em] text-[#15bee6]">
            {eyebrow}
          </div>
          <h1 className="max-w-[820px] text-[40px] font-black leading-tight tracking-[-0.05em] text-[#172033] md:text-[56px]">
            {title}
          </h1>
          {subtitle ? (
            <p className="mt-5 max-w-[760px] text-lg font-medium leading-8 text-[#62748c]">{subtitle}</p>
          ) : null}
          {cta ? (
            <Link
              href={cta.href}
              className="mt-8 inline-flex h-12 items-center justify-center rounded-lg bg-[#21c8ee] px-7 text-sm font-black text-white shadow-[0_14px_30px_rgba(33,200,238,0.28)] transition hover:-translate-y-0.5 hover:bg-[#15bde5]"
            >
              {cta.label}
            </Link>
          ) : null}
        </div>
      </section>

      <section className="bg-[#f7fafc]">
        <div className="mx-auto max-w-[1040px] px-5 py-12 sm:px-8 md:py-16">{children}</div>
      </section>
      <Footer />
    </main>
  )
}

export function ContentGrid({ children }: { children: ReactNode }) {
  return <div className="grid gap-5 md:grid-cols-2">{children}</div>
}

export function ContentCard({
  eyebrow,
  title,
  children,
}: {
  eyebrow?: string
  title: string
  children: ReactNode
}) {
  return (
    <article className="rounded-lg border border-[#dce8ef] bg-white p-6 shadow-[0_14px_34px_rgba(22,39,53,0.06)]">
      {eyebrow ? (
        <p className="mb-3 text-xs font-black uppercase tracking-[0.14em] text-[#21c8ee]">{eyebrow}</p>
      ) : null}
      <h2 className="text-xl font-black tracking-[-0.03em] text-[#172033]">{title}</h2>
      <div className="mt-4 space-y-3 text-sm font-medium leading-6 text-[#61758b]">{children}</div>
    </article>
  )
}

export function CheckList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item} className="flex gap-3">
          <span className="mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#dff9fd] text-[#11b9de]">
            <svg
              className="h-3 w-3"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              viewBox="0 0 24 24"
              aria-hidden
            >
              <path d="m5 12 4 4 10-10" />
            </svg>
          </span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  )
}

export function NoteCard({ children }: { children: ReactNode }) {
  return (
    <section className="rounded-lg border border-[#bdeef7] bg-[#eafbff] p-6 text-sm font-semibold leading-6 text-[#405268]">
      {children}
    </section>
  )
}
