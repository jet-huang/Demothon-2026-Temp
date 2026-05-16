# Demo Runbook

## 2-minute briefing outline

1. Problem statement. Travellers receive disruption SMSes that do not actually fix anything.
2. What we built. A SAM-orchestrated assistant that fans a single broker event out across four specialist agents and returns a phone-friendly re-plan.
3. The pieces. Solace event broker, SAM orchestrator + four specialist agents, fakegen-seeded SQLite, React phone-frame UI.
4. What you will see. A publisher emits one disruption. The UI shows the alert, the agent fan-out, and the re-plan card live.

## Pre-flight checklist

1. Broker reachable.
   - Verify `tcp://192.168.88.188:55555` (SMF) and `ws://192.168.88.188:8008` (WebSocket) respond.
2. SAM core up.
   - `curl http://<sam-host>:8000/health`
   - `glab` not required.
3. Agents discovered.
   - Open the WebUI agent registry view. Confirm five agents: Orchestrator, Flights, Weather, Itinerary, Images.
4. Frontend up.
   - `cd frontend && VITE_USE_MOCK=false npm run dev`
   - Open the printed URL in the demo browser tab.
5. Publisher venv ready.
   - `cd publisher && uv sync`
6. Pre-warm the orchestrator.
   - In the WebUI, send the prompt `warmup`. Wait for a response. Discard.
7. DB freshness.
   - `cd fakegen && uv run main.py refresh --db-config configs/weather.db.yaml --schema configs/weather.schema.yaml`
   - Itinerary: dates anchored at generation time. Regenerate if the demo day rolled over since the last build.

## 3-minute live keystrokes

1. T+00s. Frontend visible in phone frame. Narrate: "Idle. Awaiting any disruption on travel/flights/+/status."
2. T+10s. In the publisher terminal, paste and run:

   ```
   uv run publisher/publish_disruption.py disrupt \
     --flight JL001 --status DELAYED --minutes 180 --reason weather
   ```

3. T+12s. UI banner: "JL001 delayed 180 min". Narrate: "The broker just emitted one message. The UI received it via solclientjs WebSocket."
4. T+15s. UI shows the orchestrator firing. First agent step appears.
5. T+25s. WeatherAgent step done. Narrate destination forecast headline.
6. T+35s. ItineraryAgent step done. Shifted plan list renders.
7. T+45s. Final card visible: headline, weather, three-line shifted itinerary. Hold for the audience.
8. T+60s to T+180s. Q&A. Optional second take: a different flight number to show statelessness.

## Recovery (Plan B)

1. If the publisher does not connect within 5 s, switch terminals and run the same command from a backup laptop already on the same VPN.
2. If the UI does not receive an alert within 15 s, click the on-screen "Trigger mock alert" button to drive the demo from the mock path. Narrate honestly: "Showing the same flow against the canned event."
3. If the orchestrator stalls or returns an error, queue `docs/demo-recovery.mp4` and narrate over the recording.

## Reset between rehearsals

1. Refresh the frontend tab.
2. In the publisher terminal, ctrl-c any ambient process.
3. Optionally re-run `fakegen refresh` if the rehearsal block crosses a day boundary.
