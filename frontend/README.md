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
