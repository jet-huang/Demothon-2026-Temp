# Event Schemas

JSON Schema documents the EventMesh Gateway pastes into the Add Event Rule form (Structured Invocation section).

## Files

- flight-change.input.schema.json. Validates events received on `D/changes/flight/>`.
- flight-change.output.schema.json. Constrains the orchestrator's re-plan response.

## Topic convention

Inbound (Chaos Maker -> EventMesh Gateway):

```
D/changes/flight/{carrier}/{flight_no}/{event_type}
```

- carrier. IATA airline code, uppercase, 2 or 3 chars.
- flight_no. Full flight number, uppercase, 2 to 7 chars.
- event_type. One of: delay, cancel, gate-change, status.

Outbound (Gateway -> phone-frame after the orchestrator returns):

```
D/res/{traveler_id}/ok    # task_response:structured_output (RePlan JSON)
D/res/{traveler_id}/ng    # task_response:a2a_task_response.error
```

The gateway captures `traveler_id` from the inbound payload via
`forward_context` and substitutes it into the reply `topic_expression`
using `template:`. Each phone subscribes to `D/res/{traveler_id}/>` and
therefore only receives its own re-plan.

## Gateway configuration

1. Subscribe the gateway to `D/changes/flight/>`.
2. In Add Event Rule, paste the instruction:
   - `Process this event {payload}. As a Personal Travel assistant aware of the traveler's current on-going trip, make sure we can produce new itinerary (if needed) to fit the realtime situation.`
3. Enable Structured Invocation.
4. Input Schema. Paste flight-change.input.schema.json.
5. Output Schema. Paste flight-change.output.schema.json.

## Publishing test events

```
cd publisher
uv run publisher/publish_disruption.py disrupt \
  --traveler-id demo-traveler-001 \
  --flight JL001 --status DELAYED --minutes 180 --reason weather
```

The publisher emits to `D/changes/flight/JL/JL001/delay` with a payload conforming to the input schema. The `--traveler-id` flag is required so the gateway can route the reply on `D/res/{traveler_id}/ok`.

## Field mapping note

`traveler_id` in the public envelope and topic templates corresponds 1:1 to the `user_id` column in the SQL tables (`traveler`, `trip`, `itinerary_item`). The kiosk DAO writes `user_id = <ULID>` and the orchestrator prompt template substitutes the same value into the agent instructions.
