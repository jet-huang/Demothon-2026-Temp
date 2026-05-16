# Itinerary in Motion

Your itinerary listens to the world and re-plans itself in seconds.

Agentic AI personal travel assistant built on Solace Agent Mesh (SAM) Enterprise and Solace Event Broker. The demo headlines in-trip disruption rescue: a flight delay event flows through the broker, a fleet of specialist agents collaborates through the EventMesh Gateway, and each traveler's phone receives a proactive re-plan within seconds.

For a step-by-step setup guide on a clean machine, see [QUICK_START.md](QUICK_START.md).

Or for a live demo, check here:

[Live Demo for Demothon 2026](https://jet-huang.github.io/Demothon-2026-Temp)

## What you will see at the demo

1. A kiosk projects three randomly generated trips, each with its own QR code.
2. Three audience members scan and land on a phone-frame web app bound to their own traveler.
3. The presenter clicks "Make something happen." on one trip card.
4. The broker emits a flight-change event. The EventMesh Gateway invokes the OrchestratorAgent, which fans out to FlightsAgent, WeatherAgent, ItineraryAgent and ImagesAgent.
5. Only the targeted phone receives a re-plan card: updated flight status, destination weather at the new arrival window, and a shifted itinerary with cancelled items faded out.

## Architecture at a glance

- Solace Event Broker. Single source of truth for the disruption event and the per-traveler response.
- Solace Agent Mesh Enterprise (SAM EE). Hosts the orchestrator and specialist agents.
- EventMesh Gateway (`sam-event-mesh-gateway`). Bridges broker topics to A2A structured invocations and routes the synthesized reply back to a per-traveler topic `D/res/{traveler_id}/{ok|ng}`.
- Kiosk (FastAPI). Demo landing page, QR generator, chaos injector, and traveler bootstrap endpoint.
- Phone-frame (React + Vite + Tailwind, Solace BrandedCSS). Subscribes to its own response topic via solclientjs.
- Publisher side-car. CLI tool that still works for headless smoke tests.

## Topology

- Inbound chaos topic. `D/changes/flight/{carrier}/{flight_no}/{event_type}`. Schema in `docs/event-schemas/flight-change.input.schema.json`.
- Outbound reply topic. `D/res/{traveler_id}/{ok|ng}`. Schema in `docs/event-schemas/flight-change.output.schema.json`.
- The gateway captures `traveler_id` from the inbound payload via `forward_context` and renders the reply topic with a `template:` SAC expression.

## Repository layout

```
.
├── compose.yaml                       SAM core + broker network + kiosk
├── _base.yaml                         Shared compose service base
├── profiles/
│   ├── fy27-demothon-v1/              Active demo profile
│   │   ├── core/
│   │   │   ├── configs/agents/        Deployed agent yaml files
│   │   │   ├── db/                    SQLite files mounted into SAM core
│   │   │   ├── mock/                  Static JSON fixtures
│   │   │   ├── tools/                 Per-agent Python tools
│   │   │   ├── _shared_tools/         Tools referenced by multiple agents
│   │   │   ├── app.env                Non-secret app config
│   │   │   └── kiosk.env              Kiosk container config
│   │   ├── shared.env                 Broker creds, vpn, namespace (gitignored)
│   │   └── models.env                 LLM endpoint and key (gitignored)
│   └── _common/                       Shared env files and secrets
├── kiosk/                             FastAPI kiosk + QR + chaos
│   ├── app/                           Routes, trip factory, DAO, templates
│   ├── data/regions.json              Destination + activity catalog
│   ├── Dockerfile
│   └── docker-compose.yml             Optional standalone kiosk runner
├── frontend/                          React phone-frame
│   ├── src/                           App, ItineraryView, brokerClient
│   └── dist/                          Built bundle (served by kiosk)
├── publisher/                         Standalone chaos publisher CLI
│   └── lib.py                         Shared payload + publish helpers
├── fakegen/                           YAML-driven mock data generator
│   ├── configs/                       Per-table schema + db config
│   └── db/                            Generated SQLite outputs
├── docs/
│   ├── demo-runbook.md                3-minute live keystrokes
│   ├── demo-plan.md                   Roles, timing, risk register
│   └── event-schemas/                 JSON Schemas for inbound and outbound
├── sponsor-specific/BrandedCSS/       Solace brand spec (mounted read-only)
├── _stories/                          Story prompts driving each workstream
└── _worklog/                          Per-issue worklogs
```

## Agents

- OrchestratorAgent. Receives the structured invocation, treats the inbound event as the sole source of truth for flight status, and synthesizes the phone-friendly reply.
- FlightsAgent. Python tool `lookup_flight` against `mock/flights.json`.
- WeatherAgent. SQL plugin against `db/weather.db` plus the shared `time_tool`.
- ItineraryAgent. SQL plugin against `db/itinerary.db`. Reads per-traveler rows.
- ImagesAgent. Pixabay-backed Python tool.

## Branding

Every web surface (kiosk landing page and phone-frame) imports `sponsor-specific/BrandedCSS/index.css` and uses Solace brand utilities, NewSpirit and Figtree fonts, the Solace logo and favicon. The kiosk container mounts the brand directory read-only at `/data/brand`.

## Story history

The demo was built up story by story. Each story file lives in `_stories/` and produced one or more GitLab issues plus a worklog entry under `_worklog/`. The most recent stories address gateway plumbing, source-of-truth correctness, replanning UX, chaos scoping, and cancellation visuals.

## References

- Demo runbook. [docs/demo-runbook.md](docs/demo-runbook.md)
- Demo plan. [docs/demo-plan.md](docs/demo-plan.md)
- Event schemas. [docs/event-schemas/README.md](docs/event-schemas/README.md)
- Quick start guide. [QUICK_START.md](QUICK_START.md)
- Fakegen usage. [fakegen/README.md](fakegen/README.md)
- Publisher usage. [publisher/README.md](publisher/README.md)
