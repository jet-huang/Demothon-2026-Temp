# Quick Start

This guide walks through standing up the Itinerary in Motion demo from a clean checkout. The demo is verified on Linux, macOS, and Windows under WSL2. Native Windows shells are not supported.

## 1. Prerequisites

Install the following on the host:

1. Docker Engine 24 or newer with Compose v2.
2. Git.
3. Python 3.13. Managed transparently inside the kiosk container; only required on the host if you intend to run the publisher CLI or fakegen directly.
4. `uv` package manager. Install via `curl -LsSf https://astral.sh/uv/install.sh | sh`.
5. Node.js 20 or newer. Only required if you intend to rebuild the phone-frame bundle.
6. A reachable Solace Event Broker. Default expectation: SMF on `tcp://<host>:55555`, WebSocket on `ws://<host>:8008`, SEMP admin on `http://<host>:8080`.
7. An LLM endpoint and API key reachable from the SAM core container.
8. Modern CLI helpers recommended for working in this repo: `jq`, `yq`, `rg` (ripgrep), `fd`, `ast-grep`.

## 2. Clone

```shell
git clone <repository-url> fy27-demothon
cd fy27-demothon
```

## 3. Files you must bring yourself

The following files are gitignored and contain real credentials or environment-specific values. Create each before starting any container.

### 3.1 Root `.env`

Lives at the repository root. Selects the active profile and pins container image tags. Use the committed `.env` in your environment, or recreate from this template:

```dotenv
SAM_PROFILE=fy27-demothon-v1
SAM_MAIN_TAG=1.500.0
SAM_DEPLOYER_TAG=1.8.2
SAM_MAIN_OFFICIAL_IMAGE=your.private.cr/solace/scr/official/solace-agent-mesh-enterprise
SAM_MAIN_IMAGE=your.private.cr/solace/scr/official/solace-agent-mesh-enterprise
SAM_DEPLOYER_OFFICIAL_IMAGE=your.private.cr/solace/scr/official/sam-agent-deployer
SAM_DEPLOYER_IMAGE=your.private.cr/solace/scr/twsolace/sam-agent-deployer
DIND_IMAGE=docker:29.2-dind
MANAGEMENT_SERVER_PORT=1370
CONTAINER_ENGINE=docker
CONTAINER_NETWORK=sam-local-network
```

### 3.2 `profiles/fy27-demothon-v1/shared.env`

Broker connection and VPN. Consumed by SAM core, the deployer, and agent containers.

```dotenv
SOLACE_BROKER_URL=ws://<broker-host>:8008
SOLACE_BROKER_VPN=<vpn-name>
SOLACE_BROKER_USERNAME=<username>
SOLACE_BROKER_PASSWORD=<password>
NAMESPACE=fy27-demothon-v1/
```

### 3.3 `profiles/fy27-demothon-v1/models.env`

LLM endpoint and key.

```dotenv
LLM_SERVICE_ENDPOINT=<https-endpoint>
LLM_SERVICE_API_KEY=<key>
LLM_SERVICE_GENERAL_MODEL_NAME=<model-id>
GENERAL_MAX_TOKENS=1024
```

### 3.4 `profiles/fy27-demothon-v1/core/sam-core.env` and `core/sam-deployer.env`

Empty files are acceptable for the basic demo. Populate only if you need to override SAM defaults.

### 3.5 `profiles/_common/secrets/s3-sam.env`

S3 (SeaweedFS) credentials used by SAM artifact service. Copy `profiles/_common/secrets/sample.s3-sam.env` and edit values.

```shell
cp profiles/_common/secrets/sample.s3-sam.env profiles/_common/secrets/s3-sam.env
```

### 3.6 `_docker_config.json`

Docker registry auth used by the SAM deployer to pull private agent images. If your registry is public, an empty `{"auths":{}}` is sufficient.

```shell
echo '{"auths":{}}' > _docker_config.json
```

### 3.7 `profiles/fy27-demothon-v1/core/kiosk.env`

Broker SMF endpoint and kiosk-specific paths. Edit broker host and credentials:

```dotenv
BROKER_URL=tcp://<broker-host>:55555
BROKER_VPN=<vpn-name>
BROKER_USERNAME=<username>
BROKER_PASSWORD=<password>
KIOSK_PORT=9888
KIOSK_HOST_URL=http://<host>:9888
KIOSK_ITINERARY_DB=/data/db/itinerary.db
KIOSK_FLIGHTS_JSON=/data/mock/flights.json
KIOSK_FRONTEND_DIST=/data/frontend-dist
KIOSK_BRAND_DIR=/data/brand
```

`KIOSK_HOST_URL` must be reachable from audience phones on the same network, since it is embedded in the QR codes.

## 4. Seed the SQLite databases

The agents read SQLite files mounted into the SAM core container. Generate them with fakegen, then copy into the active profile.

```shell
cd fakegen
uv sync
uv run python main.py generate --db-config configs/weather.db.yaml   --schema configs/weather.schema.yaml
uv run python main.py generate --db-config configs/traveler.db.yaml  --schema configs/traveler.schema.yaml
uv run python main.py generate --db-config configs/trip.db.yaml      --schema configs/trip.schema.yaml
uv run python main.py generate --db-config configs/itinerary.db.yaml --schema configs/itinerary.schema.yaml
cd ..
mkdir -p profiles/fy27-demothon-v1/core/db
cp fakegen/db/*.db profiles/fy27-demothon-v1/core/db/
```

Refresh dates pre-demo if the dataset drifts past today:

```shell
cd fakegen
uv run python main.py refresh --db-config configs/weather.db.yaml --schema configs/weather.schema.yaml
cd ..
cp fakegen/db/weather.db profiles/fy27-demothon-v1/core/db/weather.db
```

## 5. Build the phone-frame bundle

The kiosk container serves the React bundle from `frontend/dist`. Build it once on the host:

```shell
cd frontend
npm install
npm run build
cd ..
```

Rebuild whenever you edit `frontend/src/`. Hot reload is not used in the kiosk-served path.

## 6. Start the SAM stack

```shell
docker compose up -d sam-dind sam-core sam-deployer
```

Wait for the SAM WebUI to respond:

```shell
curl -fsS http://localhost:8000/health
```

Open `http://localhost:8000` and confirm the agent registry lists OrchestratorAgent, FlightsAgent, WeatherAgent, ItineraryAgent, and ImagesAgent.

## 7. Start the kiosk

```shell
docker compose up -d kiosk
```

Open `http://<host>:9888/`. The kiosk renders three trip cards with QR codes under the "Itinerary in Motion" hero. Scanning any QR opens the phone-frame at `/m/{traveler_id}`.

## 8. Drive the demo

1. Audience members scan the three QR codes from the kiosk display.
2. Each phone shows its idle itinerary.
3. The presenter clicks "Make something happen." on one trip card.
4. The targeted phone shows the disruption toast, then the replanning spinner, then the re-plan card. Cancelled itinerary items fade out with a "Cancelled" badge.

## 9. Reset between rehearsals

1. Refresh each phone tab (hard refresh to drop any stale broker state).
2. On the kiosk, reload the landing page. This calls `POST /api/session` and re-seeds three fresh travelers, trips, and flights.

## 10. Headless smoke test (optional)

The original publisher CLI still works end-to-end for testing without the kiosk:

```shell
cd publisher
uv sync
uv run python publish_disruption.py disrupt \
  --traveler-id <traveler-id> \
  --flight JL001 --status DELAYED --minutes 180 --reason weather
```

Confirm the matching phone receives a re-plan card.

## Troubleshooting

### A. Phone never receives a re-plan card

1. Confirm the broker WebSocket URL in `shared.env` is reachable from the audience network. The phone connects directly to the broker, not via the kiosk.
2. Tail the SAM core logs and look for an OrchestratorAgent invocation. If absent, the EventMesh Gateway is not picking up the inbound event.
   ```shell
   docker compose logs -f sam-core | rg -i 'orchestrator|gateway|D/changes'
   ```
3. Check the broker queue subscriptions via SEMP. The gateway queue should be subscribed to `D/changes/flight/>` and have a non-zero `bindSuccessCount`.
   ```shell
   curl -s -u <admin>:<password> \
     "http://<broker-host>:8080/SEMP/v2/monitor/msgVpns/<vpn>/queues" | jq '.data[] | {queueName, bindSuccessCount, spooledMsgCount}'
   ```

### B. "Input validation failed: ... is not of type 'object'"

The gateway's structured invocation expects the raw JSON payload, not a rendered prompt string. Verify `realtime_signals_receiver_gateway.yaml` keeps `input_expression: "input:payload"` for the flight-changes handler.

### C. Re-plan card contradicts the inbound event

For example, the inbound says DELAYED but the card claims ON TIME. Confirm the orchestrator instruction in `profiles/fy27-demothon-v1/core/configs/agents/a2a_orchestrator.yaml` still treats the inbound `FlightChangeEvent` as the sole source of truth and does not call FlightsAgent for status lookup.

### D. Chaos fires against the return leg

Should not happen since chaos is pinned to the outbound leg in `kiosk/app/chaos.py`. If it does, inspect that file and confirm `leg = trip.outbound`.

### E. QR code points to localhost

`KIOSK_HOST_URL` is embedded into the QR. Set it to an address the audience phones can reach (LAN IP or DNS name), not `localhost` or `127.0.0.1`.

### F. Phone bundle is stale

The kiosk container bind-mounts `frontend/dist` read-only. Rebuild on the host with `npm run build` from `frontend/` and hard-refresh the phone tab.

### G. SAM core container exits immediately

1. Confirm `models.env` and `shared.env` exist and contain real values. Empty values yield silent startup failures.
2. Confirm the SAM image tag in the root `.env` matches an image you can pull. If you do not have access to `your.private.cr`, point `SAM_MAIN_IMAGE` at a registry you can reach.

### H. `uv` not found inside containers

The kiosk image installs `uv` during build. If the build was cached against an older base image, force a rebuild:

```shell
docker compose build --no-cache kiosk
docker compose up -d kiosk
```

### I. Broker SEMP returns 401

Default SEMP admin in this environment is `soladmin` with the password configured during broker provisioning. Adjust the curl examples accordingly.

### J. WSL2: kiosk reachable from Windows host but not from phone

Forward port 9888 from the Windows host to the WSL2 distribution, or run the kiosk container with `network_mode: host` on Linux. Confirm the firewall does not block inbound 9888 and 8008.
