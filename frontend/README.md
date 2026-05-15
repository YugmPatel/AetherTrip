# AetherTrip Frontend

Next.js + TypeScript + Tailwind CSS + shadcn/ui frontend for the AetherTrip AI travel planning engine.

## Setup

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

The frontend will connect to the backend API running on `http://localhost:8000`.

## Environment

Create `frontend/.env.local` with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_MAP_PROVIDER=geoapify
NEXT_PUBLIC_MAP_RENDERER=maplibre
NEXT_PUBLIC_GEOAPIFY_API_KEY=<geoapify_key>
```

Do not hardcode map keys in source code. Restart the Next.js dev server after changing `.env.local`; Next reads `NEXT_PUBLIC_*` values at startup.

## Build

```bash
npm run build
npm start
```

## Key Features

- **Landing Page**: Hero section with "Plan a trip" CTA, feature highlights
- **Define Your Journey**: Form-based trip input with constraints
- **Trip Results**: Itinerary display with feasibility score, budget breakdown
- **Real-time Verification**: Shows opening hours, travel times, budget accuracy

## Architecture

- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS + custom components
- **Animation**: Framer Motion
- **HTTP Client**: Axios
- **Maps**: MapLibre GL JS (ready for integration)

## API Integration

The frontend connects to the backend `POST /api/trips/plan` endpoint:

```typescript
POST http://localhost:8000/api/trips/plan
Content-Type: application/json

{
  "user_input": "Plan a 3-day LA trip from San Jose for 4 friends under $400 each..."
}
```

Response includes trip_id, itinerary, budget_report, feasibility_score, etc.

## Supabase Schema

Run `../supabase/schema.sql` in the Supabase SQL Editor before testing saved trip history. After creating or updating tables, run `notify pgrst, 'reload schema';` or refresh/restart the project if the REST API says a table is missing from the schema cache.
