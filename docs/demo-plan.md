# Demo Plan

## Goal

Show a personal travel assistant fan out a single flight disruption across four specialist agents (Flights, Weather, Itinerary, Images) over Solace Agent Mesh, with the re-plan rendered live on a phone-frame UI.

## Roles

- Presenter: drives keystrokes and narration.
- Operator: monitors the agent containers and broker, ready to switch to Plan B (recorded screen capture) on failure.

## Dependencies

1. Solace event broker reachable at `tcp://192.168.88.188:55555` (SMF) and `ws://192.168.88.188:8008` (WebSocket), VPN `ai168`.
2. SAM core running on port 8000 with all four agents discovered:
   - OrchestratorAgent
   - FlightsAgent
   - WeatherAgent
   - ItineraryAgent
   - ImagesAgent
3. Frontend started with `VITE_USE_MOCK=false`, pointing at the SAM SSE endpoint and the broker WebSocket.
4. Publisher virtualenv ready under `publisher/` with `uv sync` completed.

## Beat-by-beat target timing

1. T+00s. Presenter opens the phone-frame UI. Idle card shown.
2. T+10s. Operator runs the publisher disrupt command in a side terminal.
3. T+12s. UI receives the broker alert; disruption banner renders.
4. T+15s. UI POSTs a re-plan task to SAM; first agent step ("FlightsAgent: confirm status") appears.
5. T+25s. WeatherAgent step completes.
6. T+35s. ItineraryAgent step completes; shifted plan card renders.
7. T+45s. Final headline + weather + itinerary bullet list visible.

Total target: ≤ 60 s from publish to final card. Acceptance threshold: ≤ 30 s for the re-plan card (story 005).

## Risk register

- Cold start on the orchestrator can add 5–10 s. Mitigation: pre-warm prompt before the live take.
- Broker WebSocket port blocked behind a firewall. Mitigation: verify connectivity from the demo laptop the morning of.
- LLM rate limiting. Mitigation: keep `GENERAL_MAX_TOKENS` at 1024 and rerun once if a 429 lands.
- Plan B: pre-recorded screen capture stored at `docs/demo-recovery.mp4` (operator queues it if any of the above blocks the live take for more than 30 s).
