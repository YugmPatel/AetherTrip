# AetherTrip Frontend

Next.js + TypeScript + Tailwind frontend for the AetherTrip verification-first travel planning engine.

## What It Includes

- Landing page that explains the verification engine.
- `/plan` trip request flow with streaming agent progress.
- Trip result pages with itinerary timeline, map, place details, budget, validation warnings, source confidence, repair history, and feasibility scoring.
- Supabase auth with login, signup, callback handling, profile, and saved trip history.
- Static information pages for about, how it works, verification engine, accuracy disclaimer, privacy, and terms.

## Setup

```bash
cd frontend
npm install
copy .env.local.example .env.local
```

Configure `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_MAP_PROVIDER=geoapify
NEXT_PUBLIC_MAP_RENDERER=maplibre
NEXT_PUBLIC_GEOAPIFY_API_KEY=your_geoapify_key
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_LINKEDIN_URL=
NEXT_PUBLIC_GITHUB_REPO_URL=https://github.com/YugmPatel/AetherTrip
```

Do not hardcode API or map keys in source code. Restart the Next.js dev server after changing `NEXT_PUBLIC_*` values; Next reads them at startup.

## Development

Start the backend first on `http://localhost:8000`, then run:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Build

```bash
npm run build
npm start
```

## API Integration

The planning page uses the streaming endpoint first:

```http
POST http://localhost:8000/api/trips/plan/stream
Content-Type: application/json
Accept: text/event-stream

{
  "user_input": "Plan a 3-day LA trip from San Jose for 4 friends under $400 each"
}
```

If streaming is unavailable, the frontend falls back to:

```http
POST http://localhost:8000/api/trips/plan
```

Trip result pages can also fetch:

```http
GET http://localhost:8000/api/trips/{trip_id}
```

## Supabase

Run `../supabase/schema.sql` in the Supabase SQL Editor before testing saved trip history. If Supabase reports a schema cache error after creating or updating tables, run:

```sql
notify pgrst, 'reload schema';
```

The frontend expects Supabase public URL and anon key values for auth-aware pages and saved history.
