import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AetherTrip - Verified AI Travel Plans',
  description: 'AI travel plans that are verified before you trust them',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
