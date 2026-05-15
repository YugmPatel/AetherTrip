'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { getLoginPath, getProtectedPath, useAuthUser } from '@/lib/auth'
import Footer from '@/components/Footer'
import UserAvatar from '@/components/UserAvatar'

type IconName =
  | 'shield'
  | 'bolt'
  | 'route'
  | 'clock'
  | 'wallet'
  | 'weather'
  | 'trust'
  | 'repair'
  | 'audit'
  | 'feasible'
  | 'train'
  | 'museum'
  | 'mountain'
  | 'alert'
  | 'check'
  | 'arrow'

type Feature = {
  icon: IconName
  title: string
  description: string
  highlighted?: boolean
}

const metrics = [
  { value: '4+', label: 'Grounded Sources' },
  { value: '7', label: 'Validation Layers' },
  { value: 'Repair', label: 'Issue Handling' },
  { value: 'MVP', label: 'Private Beta' },
]

const verificationLayers: Feature[] = [
  {
    icon: 'route',
    title: 'Route Logic',
    description:
      'Checks actual travel times between locations, accounting for traffic patterns and public transit schedules.',
    highlighted: true,
  },
  {
    icon: 'clock',
    title: 'Live Hours',
    description:
      'Verifies opening and closing times for every museum, restaurant, and landmark in real-time.',
  },
  {
    icon: 'wallet',
    title: 'Hidden Costs',
    description:
      'Estimates taxes, local tipping customs, and dynamic entry fees to prevent budget surprises.',
  },
  {
    icon: 'weather',
    title: 'Climate Sync',
    description:
      'Monitors seasonal weather patterns to suggest the best days for outdoor activities.',
  },
  {
    icon: 'trust',
    title: 'Trust Scoring',
    description:
      'Shows how much of the itinerary passed feasibility checks using available data at generation time.',
  },
  {
    icon: 'repair',
    title: 'Auto-Repair',
    description:
      'If a conflict is found, our system automatically shifts bookings or finds alternatives.',
    highlighted: true,
  },
  {
    icon: 'audit',
    title: 'Place Audit',
    description:
      'Cross-references multiple data sources to confirm businesses are still active and reputable.',
  },
  {
    icon: 'feasible',
    title: 'Instant Feasibility',
    description:
      'Get a validation report with warnings, repairs, and items that may need review.',
  },
]

const repairRows = [
  {
    icon: 'museum' as const,
    title: 'Ghibli Museum Visit',
    note: 'Shifted: Opening hours updated to 10 AM',
    state: 'Fixed',
  },
  {
    icon: 'train' as const,
    title: 'Shinkansen Transfer',
    note: 'Verified: 15 min buffer added for rush',
    state: 'Verified',
  },
  {
    icon: 'mountain' as const,
    title: 'Mt. Fuji Viewpoint',
    note: 'Optimized: Moved to Wed (Better Weather)',
    state: 'Fixed',
  },
]

const principleRows = [
  {
    title: 'Verification Over Generation',
    description:
      'Traditional AI creates "ideal" plans. We create verified plans that account for reality.',
  },
  {
    title: 'Dynamic Repair Cycles',
    description:
      'If a venue closes or transit fails, the engine instantly re-routes your entire day.',
  },
  {
    title: 'Budget-First Constraints',
    description:
      'Every repair respects your initial budget constraints, ensuring no accidental overspending.',
  },
]

function Icon({ name, className = 'h-5 w-5' }: { name: IconName; className?: string }) {
  const common = {
    className,
    fill: 'none',
    stroke: 'currentColor',
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    strokeWidth: 2,
    viewBox: '0 0 24 24',
    'aria-hidden': true,
  }

  switch (name) {
    case 'shield':
      return (
        <svg {...common}>
          <path d="M12 3 5.5 5.7v5.8c0 4.1 2.7 7.8 6.5 9.1 3.8-1.3 6.5-5 6.5-9.1V5.7L12 3Z" />
          <path d="m9.4 12.1 1.7 1.7 3.7-4.1" />
        </svg>
      )
    case 'bolt':
      return (
        <svg {...common}>
          <path d="m13 2-7 12h5l-1 8 8-13h-5l0-7Z" />
        </svg>
      )
    case 'route':
      return (
        <svg {...common}>
          <path d="M6 19c2.7-5.6 9.3-2.4 12-8" />
          <path d="M7.5 5.5 11 2l3.5 3.5L11 9 7.5 5.5Z" />
          <path d="M4 19.5h4" />
          <path d="M16 11h4" />
        </svg>
      )
    case 'clock':
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
          <path d="M12 7.5v5l3 1.8" />
        </svg>
      )
    case 'wallet':
      return (
        <svg {...common}>
          <path d="M4 7.5A2.5 2.5 0 0 1 6.5 5H18v14H6.5A2.5 2.5 0 0 1 4 16.5v-9Z" />
          <path d="M4 8h15.5v4.5H16a2 2 0 0 0 0 4h3.5V19" />
          <path d="M16 14.5h.01" />
        </svg>
      )
    case 'weather':
      return (
        <svg {...common}>
          <path d="M12 5V3" />
          <path d="m17 7 1.4-1.4" />
          <path d="M19 12h2" />
          <path d="M5 12H3" />
          <path d="m5.6 5.6 1.4 1.4" />
          <path d="M16.8 16.4a4 4 0 0 0-7.6-2.1A3 3 0 1 0 6 19h10.5a2.5 2.5 0 0 0 .3-5Z" />
          <path d="M9.2 9.4A4 4 0 0 1 16 11.7" />
        </svg>
      )
    case 'trust':
      return (
        <svg {...common}>
          <path d="M12 3 5.5 5.5v6.2c0 3.8 2.4 7.2 6.5 8.8 4.1-1.6 6.5-5 6.5-8.8V5.5L12 3Z" />
          <path d="m9.3 12 1.8 1.8 3.8-4" />
        </svg>
      )
    case 'repair':
      return (
        <svg {...common}>
          <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L4.5 16.5a2.1 2.1 0 0 0 3 3l4.8-4.8a4 4 0 0 0 5.4-5.4l-3 3-3-3 3-3Z" />
        </svg>
      )
    case 'audit':
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
          <path d="m9.3 12 1.8 1.8 3.8-4" />
        </svg>
      )
    case 'feasible':
      return (
        <svg {...common}>
          <path d="m13 2-8 12h6l-1 8 9-13h-6l0-7Z" />
        </svg>
      )
    case 'train':
      return (
        <svg {...common}>
          <path d="M7 4h10a2 2 0 0 1 2 2v8a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V6a2 2 0 0 1 2-2Z" />
          <path d="M8 9h8" />
          <path d="M8.5 18 7 21" />
          <path d="M15.5 18 17 21" />
          <path d="M8.5 14h.01" />
          <path d="M15.5 14h.01" />
        </svg>
      )
    case 'museum':
      return (
        <svg {...common}>
          <path d="M4 10h16" />
          <path d="M6 10v8" />
          <path d="M10 10v8" />
          <path d="M14 10v8" />
          <path d="M18 10v8" />
          <path d="M3 18h18" />
          <path d="m12 4 8 4H4l8-4Z" />
        </svg>
      )
    case 'mountain':
      return (
        <svg {...common}>
          <path d="m3 19 7-12 4 7 2-3 5 8H3Z" />
          <path d="m10 7 1.8 3h-3.5L10 7Z" />
        </svg>
      )
    case 'alert':
      return (
        <svg {...common}>
          <path d="M12 9v4" />
          <path d="M12 17h.01" />
          <path d="M10.3 3.9 2.8 17a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
        </svg>
      )
    case 'check':
      return (
        <svg {...common}>
          <path d="m5 12 4 4 10-10" />
        </svg>
      )
    case 'arrow':
      return (
        <svg {...common}>
          <path d="M5 12h14" />
          <path d="m13 6 6 6-6 6" />
        </svg>
      )
    default:
      return null
  }
}

function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2.5" aria-label="AetherTrip home">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#21c8ee] text-white shadow-[0_8px_22px_rgba(33,200,238,0.28)]">
        <Icon name="shield" className="h-5 w-5" />
      </span>
      <span className="text-[17px] font-black tracking-tight text-[#21c8ee]">AetherTrip</span>
    </Link>
  )
}

function MetricBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-[10px] font-bold">
        <span className="text-[#20242c]">{label}</span>
        <span className="text-emerald-500">{value}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[#e7eef2]">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.9, delay: 0.35, ease: 'easeOut' }}
          className="h-full rounded-full bg-[#21c8ee]"
        />
      </div>
    </div>
  )
}

function AvatarStack() {
  const avatars = [
    {
      src: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=96&h=96&q=80',
      alt: 'Nomad traveler smiling outdoors',
    },
    {
      src: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=96&h=96&q=80',
      alt: 'Remote worker traveler portrait',
    },
    {
      src: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=96&h=96&q=80',
      alt: 'Digital nomad profile portrait',
    },
    {
      src: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=96&h=96&q=80',
      alt: 'Traveler profile portrait',
    },
  ]

  return (
    <div className="flex items-center">
      <div className="flex -space-x-2">
        {avatars.map((avatar) => (
          <img
            key={avatar.src}
            src={avatar.src}
            alt={avatar.alt}
            className="h-8 w-8 rounded-full border-2 border-white object-cover shadow-sm"
          />
        ))}
        <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-white text-[9px] font-black text-[#20242c] shadow-sm">
          +12k
        </span>
      </div>
      <span className="ml-4 text-xs font-medium text-[#8a919b]">Trusted by global nomads</span>
    </div>
  )
}

function VerificationPanel() {
  return (
    <motion.div
      initial={{ opacity: 0, rotateX: 8, y: 24 }}
      animate={{ opacity: 1, rotateX: 0, y: 0 }}
      transition={{ duration: 0.75, delay: 0.1, ease: 'easeOut' }}
      className="hero-card-tilt relative mx-auto w-full max-w-[420px]"
    >
      <div className="overflow-hidden rounded-[10px] border border-[#e8eef2] bg-white shadow-[0_26px_65px_rgba(11,31,44,0.12)]">
        <div className="flex items-center justify-between border-b border-[#dde5ea] px-6 py-5">
          <div>
            <h2 className="text-base font-extrabold tracking-[-0.01em] text-[#171b22]">
              Tokyo &amp; Kyoto Circuit
            </h2>
            <p className="mt-0.5 text-xs font-medium text-[#59616c]">7 Days &bull; Verified Itinerary</p>
          </div>
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#dffaf1] text-emerald-500">
            <Icon name="shield" className="h-4 w-4" />
          </span>
        </div>

        <div className="grid gap-6 px-6 py-8 sm:grid-cols-[150px_1fr]">
          <div className="relative flex h-[146px] items-center justify-center">
            <svg className="h-[146px] w-[146px] -rotate-90" viewBox="0 0 160 160" aria-hidden>
              <circle cx="80" cy="80" r="62" fill="none" stroke="#edf4f7" strokeWidth="12" />
              <motion.circle
                cx="80"
                cy="80"
                r="62"
                fill="none"
                stroke="#24c9ed"
                strokeLinecap="round"
                strokeWidth="12"
                strokeDasharray="389"
                initial={{ strokeDashoffset: 389 }}
                animate={{ strokeDashoffset: 31 }}
                transition={{ duration: 1.1, ease: 'easeOut' }}
              />
            </svg>
            <div className="absolute text-center">
              <div className="text-[32px] font-black leading-none tracking-[-0.04em] text-[#171b22]">92</div>
              <div className="mt-1 text-[8px] font-black uppercase tracking-[0.16em] text-[#98a0aa]">Score</div>
            </div>
          </div>

          <div className="flex flex-col justify-center">
            <p className="mb-4 text-[11px] font-black uppercase tracking-[0.14em] text-[#2e333b]">
              Verification Metrics
            </p>
            <div className="space-y-3">
              <MetricBar label="Route Logic" value={100} />
              <MetricBar label="Budget Sync" value={98} />
              <MetricBar label="Repair Stability" value={85} />
            </div>
          </div>
        </div>

        <div className="px-6 pb-6">
          <div className="mb-3 flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.1em] text-[#2e333b]">
            <Icon name="repair" className="h-3.5 w-3.5" />
            Recent Auto-Repairs
          </div>

          <div className="space-y-3">
            {repairRows.map((row, index) => (
              <motion.div
                key={row.title}
                initial={{ opacity: 0, x: 18 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.45, delay: 0.35 + index * 0.12 }}
                className="flex items-center gap-3 rounded-lg border border-[#edf2f4] bg-[#fbfdfe] p-3 shadow-[0_8px_18px_rgba(22,39,53,0.04)]"
              >
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-md ${
                    row.state === 'Verified' ? 'bg-emerald-50 text-emerald-500' : 'bg-cyan-50 text-[#21c8ee]'
                  }`}
                >
                  <Icon name={row.icon} className="h-3.5 w-3.5" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[11px] font-black text-[#171b22]">{row.title}</span>
                  <span className="block truncate text-[9px] font-semibold text-[#74808b]">{row.note}</span>
                </span>
                <span
                  className={`rounded-full border px-2 py-1 text-[9px] font-black uppercase ${
                    row.state === 'Verified'
                      ? 'border-emerald-300 bg-emerald-50 text-emerald-600'
                      : 'border-cyan-300 bg-cyan-50 text-[#119fc1]'
                  }`}
                >
                  {row.state}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 14, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.55, delay: 0.75, ease: 'easeOut' }}
        className="absolute -bottom-5 -left-10 hidden w-[190px] rounded-xl border border-[#edf2f4] bg-white p-4 shadow-[0_20px_40px_rgba(11,31,44,0.18)] md:block"
      >
        <div className="flex gap-3">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-orange-50 text-orange-400">
            <Icon name="alert" className="h-4 w-4" />
          </span>
          <div>
            <p className="text-[11px] font-black text-[#171b22]">Hidden Cost Alert</p>
            <p className="mt-1 text-[9px] font-semibold leading-snug text-[#74808b]">
              Taxes &amp; tips included in total.
            </p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

function DashboardVisual() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 26, rotateX: 8 }}
      whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
      viewport={{ once: true, amount: 0.4 }}
      transition={{ duration: 0.75, ease: 'easeOut' }}
      className="dashboard-float relative mx-auto w-full max-w-[500px] rounded-xl border-4 border-white bg-[#cbf4fb] p-7 shadow-[0_28px_80px_rgba(36,102,123,0.28)]"
    >
      <div className="overflow-hidden rounded-md bg-[#213e56] p-3 shadow-inner">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[#ff7d72]" />
            <span className="h-2 w-2 rounded-full bg-[#ffd166]" />
            <span className="h-2 w-2 rounded-full bg-[#28d5a7]" />
          </div>
          <span className="text-[8px] font-black uppercase tracking-[0.25em] text-[#9fd8e4]">
            AetherTrip Dashboard
          </span>
        </div>

        <div className="grid min-h-[168px] grid-cols-[82px_1fr_88px] gap-3">
          <div className="space-y-3">
            <div className="rounded-md bg-[#2b5873] p-2">
              <div className="mb-2 h-2 w-10 rounded-full bg-[#49d2ec]" />
              <div className="flex h-12 items-end gap-1">
                {[38, 54, 70, 45, 82].map((height) => (
                  <span
                    key={height}
                    className="w-2 rounded-t bg-[#49d2ec]"
                    style={{ height: `${height}%` }}
                  />
                ))}
              </div>
            </div>
            <div className="rounded-md bg-[#2b5873] p-2">
              <div className="h-12 rounded-full border-[7px] border-[#49d2ec] border-r-[#40687f]" />
            </div>
          </div>

          <div className="relative rounded-md bg-[#284d68] p-3">
            <div className="absolute inset-0 opacity-60">
              <svg viewBox="0 0 220 130" className="h-full w-full" aria-hidden>
                <path
                  d="M17 65c25-25 44-26 68-17 22 8 39 3 58-16 13-13 33-8 48 12"
                  fill="none"
                  stroke="#74d6ef"
                  strokeWidth="2"
                />
                <path
                  d="M35 88c25-8 42-4 64 12 31 22 62 6 88-19"
                  fill="none"
                  stroke="#a9e8f2"
                  strokeWidth="1.5"
                  strokeDasharray="4 5"
                />
                <circle cx="78" cy="54" r="4" fill="#ff8d91" />
                <circle cx="145" cy="70" r="4" fill="#59e0b1" />
                <circle cx="180" cy="42" r="4" fill="#49d2ec" />
              </svg>
            </div>
            <div className="absolute bottom-3 left-3 right-3 flex justify-between gap-2">
              {['KYT', 'TOKYO', 'NAGOYA', 'FUJI'].map((city) => (
                <span
                  key={city}
                  className="flex-1 rounded-full bg-[#49d2ec]/85 py-1 text-center text-[7px] font-black text-[#173449]"
                >
                  {city}
                </span>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <div className="rounded-md bg-[#2b5873] p-3 text-center">
              <Icon name="repair" className="mx-auto h-8 w-8 text-[#49d2ec]" />
              <p className="mt-2 text-[7px] font-black uppercase text-[#bfeef7]">Automatic Repair</p>
            </div>
            <div className="space-y-1.5 rounded-md bg-[#2b5873] p-2">
              {[78, 92, 65].map((width) => (
                <span key={width} className="block h-2 rounded-full bg-[#49d2ec]" style={{ width: `${width}%` }} />
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="absolute bottom-5 left-5 right-5 rounded-xl bg-white/95 px-5 py-3 shadow-[0_16px_38px_rgba(22,39,53,0.12)] backdrop-blur">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.08em] text-[#21c8ee]">Route Verification</p>
            <p className="mt-0.5 text-sm font-black text-[#171b22]">Zurich to Interlaken Express</p>
          </div>
          <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-[10px] font-black uppercase text-emerald-600">
            Validated
          </span>
        </div>
      </div>
    </motion.div>
  )
}

export default function Home() {
  const user = useAuthUser()
  const plannerPath = getProtectedPath(user, '/plan')

  return (
    <main className="min-h-screen bg-white text-[#171b22]">
      <header className="sticky top-0 z-30 border-b border-[#e8edf1] bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1180px] items-center justify-between px-5 sm:px-8">
          <Logo />
          {user ? (
            <div className="flex items-center gap-7">
              <nav className="hidden items-center gap-6 text-xs font-bold md:flex">
                <Link href="/plan" className="text-[#14bfe8] transition hover:text-[#0aaed3]">
                  New Plan
                </Link>
                <Link href="/history" className="text-[#171b22] transition hover:text-[#21c8ee]">
                  History
                </Link>
              </nav>
              <Link href="/profile" className="flex items-center gap-3 rounded-full px-2 py-1 transition hover:bg-slate-50">
                <span className="hidden max-w-[150px] text-right sm:block">
                  <span className="block truncate text-[11px] font-medium text-[#4c5562]">{user.name}</span>
                  <span className="block truncate text-xs font-black text-[#21c8ee]">{user.email}</span>
                </span>
                <UserAvatar user={user} size="sm" showStatus />
              </Link>
            </div>
          ) : (
            <nav className="flex items-center gap-6">
              <Link href={getLoginPath('/plan')} className="text-xs font-bold text-[#171b22] transition hover:text-[#21c8ee]">
                Login
              </Link>
              <Link
                href={plannerPath}
                className="rounded-lg bg-[#21c8ee] px-5 py-2.5 text-xs font-black text-white shadow-[0_10px_22px_rgba(33,200,238,0.25)] transition hover:-translate-y-0.5 hover:bg-[#15bde5]"
              >
                Get Started
              </Link>
            </nav>
          )}
        </div>
      </header>

      <section className="relative overflow-hidden border-b border-[#dce5ea] bg-[linear-gradient(105deg,#ffffff_0%,#ffffff_54%,#e7fbff_100%)]">
        <div className="mx-auto grid max-w-[1180px] items-center gap-12 px-5 py-16 sm:px-8 md:py-24 lg:grid-cols-[1fr_460px] lg:gap-16">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, ease: 'easeOut' }}
            className="max-w-[650px]"
          >
            <div className="mb-8 flex h-5 max-w-[610px] items-center rounded-full border border-[#b5edf7] bg-[#dff9fd] px-3 text-[10px] font-black uppercase tracking-[0.12em] text-[#10bfe7]">
              <Icon name="bolt" className="mr-2 h-3 w-3" />
              Next-Gen Travel Engine
            </div>

            <h1 className="max-w-[610px] text-[44px] font-black leading-[0.98] tracking-[-0.045em] text-[#171b22] sm:text-[58px] lg:text-[64px]">
              AI travel plans that are <span className="text-[#21c8ee]">verified</span> before you trust them.
            </h1>

            <p className="mt-8 max-w-[510px] text-lg font-medium leading-8 text-[#6e7580]">
              AetherTrip checks routes, opening hours, budget, weather, and hidden costs - then repairs broken
              itineraries automatically.
            </p>

            <div className="mt-14">
              <AvatarStack />
            </div>
          </motion.div>

          <VerificationPanel />
        </div>
      </section>

      <section className="border-b border-[#dce5ea] bg-[#fbfcfd]">
        <div className="mx-auto grid max-w-[1180px] grid-cols-2 px-5 py-10 text-center sm:px-8 md:grid-cols-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="py-4">
              <p className="text-[28px] font-black leading-none tracking-[-0.04em] text-[#171b22]">{metric.value}</p>
              <p className="mt-3 text-[10px] font-black uppercase tracking-[0.18em] text-[#2f343b]">{metric.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="engine" className="bg-white py-20 md:py-24">
        <div className="mx-auto max-w-[1180px] px-5 sm:px-8">
          <div className="mx-auto mb-14 max-w-[650px] text-center">
            <h2 className="text-[34px] font-black tracking-[-0.04em] text-[#171b22] md:text-[38px]">
              The 8-Layer Verification Engine
            </h2>
            <p className="mt-4 text-base font-medium leading-7 text-[#626a74]">
              We don't just generate text. Every itinerary passes through specialized validation layers to check
              feasibility using available data at generation time.
            </p>
          </div>

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {verificationLayers.map((feature, index) => (
              <motion.article
                key={feature.title}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.25 }}
                transition={{ duration: 0.45, delay: index * 0.04 }}
                className={`min-h-[176px] rounded-lg border p-6 transition hover:-translate-y-1 hover:shadow-[0_20px_45px_rgba(21,41,52,0.08)] ${
                  feature.highlighted
                    ? 'border-[#8ee8f7] bg-[#eafcff]'
                    : 'border-[#edf1f3] bg-white shadow-[0_12px_30px_rgba(22,39,53,0.03)]'
                }`}
              >
                <span
                  className={`mb-6 flex h-11 w-11 items-center justify-center rounded-xl ${
                    feature.highlighted ? 'bg-[#21c8ee] text-white' : 'bg-[#f2f4f7] text-[#2e333b]'
                  }`}
                >
                  <Icon name={feature.icon} className="h-5 w-5" />
                </span>
                <h3 className="text-base font-black tracking-[-0.01em] text-[#171b22]">{feature.title}</h3>
                <p className="mt-3 text-[13px] font-medium leading-6 text-[#5f6873]">{feature.description}</p>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      <section id="repair" className="border-y border-[#d4e8ef] bg-[#eafbff] py-20 md:py-24">
        <div className="mx-auto grid max-w-[1180px] items-center gap-12 px-5 sm:px-8 lg:grid-cols-[1fr_1fr] lg:gap-16">
          <motion.div
            initial={{ opacity: 0, x: -18 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="max-w-[520px]"
          >
            <h2 className="text-[34px] font-black leading-[1.05] tracking-[-0.04em] text-[#171b22] md:text-[38px]">
              Our AI doesn't just plan.
              <br />
              It fixes what's broken.
            </h2>

            <div className="mt-8 space-y-7">
              {principleRows.map((row) => (
                <div key={row.title} className="flex gap-4">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#bff5ff] text-[#21c8ee]">
                    <Icon name="check" className="h-4 w-4" />
                  </span>
                  <div>
                    <h3 className="text-[15px] font-black text-[#171b22]">{row.title}</h3>
                    <p className="mt-1 text-[14px] font-medium leading-6 text-[#5d6772]">{row.description}</p>
                  </div>
                </div>
              ))}
            </div>

            <Link
              href={plannerPath}
              className="mt-9 inline-flex h-12 items-center justify-center rounded-lg border border-[#9aa6b2] bg-white px-8 text-sm font-black text-[#171b22] transition hover:-translate-y-0.5 hover:border-[#21c8ee] hover:text-[#0aaed3]"
            >
              Experience the Engine
            </Link>
          </motion.div>

          <DashboardVisual />
        </div>
      </section>

      <section className="bg-[linear-gradient(90deg,#ffffff_0%,#f4fdff_50%,#ffffff_100%)] py-24 text-center md:py-28">
        <div className="mx-auto max-w-[760px] px-5 sm:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.5 }}
            transition={{ duration: 0.55, ease: 'easeOut' }}
          >
            <h2 className="text-[36px] font-black leading-tight tracking-[-0.045em] text-[#171b22] md:text-[44px]">
              Ready for a trip that actually works?
            </h2>
            <p className="mx-auto mt-5 max-w-[590px] text-base font-medium leading-7 text-[#6a737f]">
              Move from hallucinated ideas to checked, high-feasibility itineraries with visible warnings, repairs, and
              review notes.
            </p>
            <Link
              href={plannerPath}
              className="mt-8 inline-flex h-14 items-center justify-center gap-3 rounded-full bg-[#21c8ee] px-10 text-base font-black text-white shadow-[0_18px_35px_rgba(33,200,238,0.36)] transition hover:-translate-y-0.5 hover:bg-[#16bfe5]"
            >
              Start My Verified Plan
              <Icon name="arrow" className="h-5 w-5" />
            </Link>
            <p className="mt-6 flex items-center justify-center gap-2 text-xs font-semibold text-[#6d7680]">
              <span className="flex h-4 w-4 items-center justify-center rounded-full border border-emerald-400 text-emerald-500">
                <Icon name="check" className="h-2.5 w-2.5" />
              </span>
              No credit card required to start
            </p>
          </motion.div>
        </div>
      </section>

      <Footer />
    </main>
  )
}
