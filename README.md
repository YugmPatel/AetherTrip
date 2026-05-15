# AetherTrip

Travel planning with verification built in.

AetherTrip is an AI-powered trip planner that turns a natural-language request into a grounded itinerary. The backend gathers real place, route, weather, knowledge, and image data; validates the plan against practical constraints; repairs obvious conflicts; and returns a feasibility score with transparent warnings. The frontend is a Next.js app for planning, reviewing, saving, and revisiting trips.

## Current Highlights

- Natural-language trip requests with structured constraint extraction.
- Streaming planning progress from the backend so users can see each agent stage run.
- Grounded data from Geoapify Places and geocoding, OpenRouteService routing, Open-Meteo weather, and Wikidata/Wikipedia/Wikimedia enrichment.
- Day-by-day itinerary generation with place metadata, maps, images, budget estimates, validation notes, and source confidence.
- Validation layers for opening hours, route timing, budget, weather risk, source confidence, and user constraints.
- Auto-repair loop for fixable itinerary issues before the final plan is returned.
- Feasibility score, budget breakdown, validation warnings, repair history, and "why this trip works" explanation.
- Supabase-backed authentication, profiles, and saved trip history.
- Modern Next.js + TypeScript + Tailwind frontend with landing, planning, result, history, profile, auth, and static information pages.

## Architecture

```text
User request
  -> FastAPI API
  -> LangGraph workflow
     -> InputAnalyzerAgent
     -> ConstraintExtractorAgent
     -> GroundingDataFetcher
        -> Geoapify geocoding and places
        -> OpenRouteService route matrix
        -> Open-Meteo weather
        -> Wikidata/Wikipedia/Wikimedia enrichment
     -> ItineraryBuilderAgent
     -> Validators
        -> opening hours
        -> route time
        -> budget
        -> weather
        -> constraints/source confidence
     -> RepairAgent when critical issues are fixable
     -> FeasibilityScorer
     -> ExplanationAgent
  -> Next.js result experience
```

## Tech Stack

- Backend: FastAPI, LangGraph, Pydantic, OpenAI-compatible OpenRouter client, Ollama fallback, httpx.
- Frontend: Next.js 14, React, TypeScript, Tailwind CSS, Framer Motion, MapLibre-ready maps.
- Data and auth: Supabase auth, profiles, and trip history tables.
- External services: Geoapify, OpenRouteService, Open-Meteo, Wikidata, Wikipedia, Wikimedia Commons.

## Project Structure

```text
AetherTrip/
  backend/
    agents/              # Input analysis, constraints, itinerary, repair, explanation
    schemas/             # Pydantic request/response and domain models
    scoring/             # Feasibility scoring
    services/            # LLM, places, routing, weather, images, cache, budget
    validators/          # Budget, opening hours, route, weather, constraints
    graph.py             # LangGraph workflow
    main.py              # FastAPI app and API endpoints
    state.py             # Shared workflow state
  frontend/
    app/                 # Next.js routes
    components/          # UI components for planning and trip results
    lib/                 # API, auth, Supabase, storage, maps, normalization helpers
    package.json
  supabase/
    schema.sql           # Profiles/trips tables and RLS policies
  scripts/               # Debug helpers for itinerary generation
  tests/                 # Backend and frontend-adjacent regression tests
  requirements.txt
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- API keys for the services you want to run against live data
- Supabase project for auth and saved trip history

## Backend Setup

Install Python dependencies from the repo root:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a root `.env` file:

```env
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openai/gpt-4-turbo

GEOAPIFY_API_KEY=your_geoapify_key
OPENROUTESERVICE_API_KEY=your_openrouteservice_key
WIKIMEDIA_USER_AGENT=AetherTrip/1.0 (you@example.com)

# Optional local fallback
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5:7b

# Optional tuning
CACHE_TTL_HOURS=24
MAX_REPAIR_ATTEMPTS=3
BUDGET_EMERGENCY_BUFFER_PERCENT=0.05
```

Run the API:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Check health:

```bash
curl http://localhost:8000/api/health
```

## Frontend Setup

Install frontend dependencies:

```bash
cd frontend
npm install
```

Create `frontend/.env.local` from the example:

```bash
copy .env.local.example .env.local
```

Fill in:

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

Run the app:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Supabase Setup

1. Create a Supabase project.
2. Enable the auth providers you want to use. The app includes email OTP and Google OAuth flows.
3. Add `http://localhost:3000/auth/callback` as a local redirect URL.
4. Run `supabase/schema.sql` in the Supabase SQL Editor.
5. If the REST API reports a schema cache issue, run:

```sql
notify pgrst, 'reload schema';
```

The schema creates `profiles` and `trips` tables with row-level security so users can only access their own saved data.

## API Endpoints

- `GET /api/health` - backend health check.
- `POST /api/trips/plan` - create a trip plan and return the final response.
- `POST /api/trips/plan/stream` - stream pipeline events with the final trip response.
- `GET /api/trips/{trip_id}` - fetch a trip from the backend's in-memory store.

The main trip response includes parsed constraints, itinerary days, place candidates, budget report, validation reports, repair history, feasibility score, service status, warnings, and errors.

## Testing

Run backend tests from the repo root:

```bash
python -m pytest tests
```

Run frontend checks from `frontend/`:

```bash
npm run build
npm run lint
```

## Development Notes

- The backend stores generated trips in memory for direct API retrieval. Signed-in users save persistent history through Supabase from the frontend.
- The planner validates available data at generation time, but it cannot guarantee future opening hours, prices, availability, closures, weather, routes, or booking inventory.
- Missing API keys will cause some grounding services to fail or skip; the response includes service status and warnings so failures are visible.
- `.cache/` and `logs/` are local runtime directories and are intentionally ignored.

## Repository

GitHub: https://github.com/YugmPatel/AetherTrip
