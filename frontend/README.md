# frontend

Phone-frame React app simulating the traveler-facing mobile app for the Solace travel-assistant demo. Vite + React + TypeScript + Tailwind.

## Run

```shell
npm install
npm run dev
```

Default mode is `VITE_USE_MOCK=true`: the broker subscription and SAM SSE calls return pre-canned data so the UI runs without backend services. Click "Trigger flight disruption" inside the phone frame to play through the demo beats.

## Live mode (during integration)

Set `.env.local`:

```
VITE_USE_MOCK=false
VITE_SAM_BASE=http://localhost:8000
```

- `src/lib/brokerClient.ts` — stubbed; integration target is solclientjs SMF over WebSocket against `ws://192.168.88.188:8008`, subscribing to `travel/flights/+/status`. Falls back to the in-UI trigger button until wired.
- `src/lib/samClient.ts` — sends a structured prompt to SAM's WebUI backend (`/api/v2/tasks`) and parses the SSE stream. Final payload shape is finalized during the C5 dry run.

## Layout

- `src/App.tsx` — top-level state machine: itinerary → alert → agent flow → re-plan → accepted.
- `src/components/` — `PhoneFrame`, `StatusBar`, `ItineraryView`, `AlertCard`, `AgentFlow`, `RePlanCard`.
- `src/lib/mockData.ts` — traveler, flight, itinerary, alert, replan fixtures (kept in sync with `mockgen/seeds/storyline.yaml`).
- `src/types.ts` — shared TS types.
