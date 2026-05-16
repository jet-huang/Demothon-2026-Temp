# publisher

Standalone Python side-car that publishes events into the already-running Solace broker for the travel demo. Two subcommands:

- `disrupt` — one-shot flight disruption event on `travel/flights/<FLIGHT>/status`. This is the trigger the booth operator presses during the live demo.
- `ambient` — periodic heartbeat events on `travel/telemetry/heartbeat/<seq>` so the broker visibly "breathes" during rehearsal.

## Broker connection

Defaults match the local stack in `~/repo/ai-demo-for-solace-agent-mesh/profiles/1.171.0-clean-start/shared.env`:

- `BROKER_URL=tcp://192.168.88.188:55555`
- `BROKER_VPN=ai168`
- `BROKER_USERNAME=user01`
- `BROKER_PASSWORD=password`

Override any of them with environment variables of the same name.

## Usage

```shell
uv run python publish_disruption.py disrupt --flight JL001 --status DELAYED --minutes 180 --reason weather
uv run python publish_disruption.py ambient --interval 3
```
