#!/usr/bin/env bash
set -euo pipefail

AGENT_ID="${1:-}"
AGENT_ENV_FILE="${2:-}"
AGENT_CONFIG_FILE="${3:-}"

if [[ -z "${AGENT_ID}" ]]; then
  echo "Error: Agent ID required as first argument" >&2
  exit 1
fi
if [[ -z "${AGENT_ENV_FILE}" ]]; then
  echo "Error: env file path required as second argument" >&2
  exit 1
fi
if [[ -z "${AGENT_CONFIG_FILE}" ]]; then
  echo "Error: agent YAML path required as third argument" >&2
  exit 1
fi
CONTAINER_ENGINE="${CONTAINER_ENGINE:-docker}"
CONTAINER_NAME="agent-${AGENT_ID}"
SAM_DEBUG="${SAM_DEBUG:-false}"

debug_log() {
  if [[ "${SAM_DEBUG}" == "true" ]]; then
    echo "[DEBUG] $*" >&2
  fi
}

if [[ "${SAM_DEBUG}" == "true" ]]; then
  echo "[DEBUG] Environment variables loaded:" >&2
  cat "${AGENT_ENV_FILE}" >&2
  echo "" >&2
  echo "[DEBUG] Agent configuration:" >&2
  cat "${AGENT_CONFIG_FILE}" >&2
  echo "" >&2
fi

# Stop and remove existing container if it exists
if "${CONTAINER_ENGINE}" inspect "${CONTAINER_NAME}" &>/dev/null; then
  debug_log "Stopping container ${CONTAINER_NAME}"
  "${CONTAINER_ENGINE}" stop "${CONTAINER_NAME}"

  debug_log "Removing container ${CONTAINER_NAME}"
  "${CONTAINER_ENGINE}" rm "${CONTAINER_NAME}"
else
  debug_log "Container ${CONTAINER_NAME} does not exist, skipping stop/remove"
fi

# Deploy updated container
debug_log "Deploying updated container ${CONTAINER_NAME} using ${CONTAINER_ENGINE}"
"${CONTAINER_ENGINE}" run -d \
  --restart unless-stopped \
  -v "${AGENT_CONFIG_FILE}:/agent.yaml" \
  -e "DATABASE_URL=sqlite:///agent_${AGENT_ID}.db" \
  --env-file "${AGENT_ENV_FILE}" \
  --name "${CONTAINER_NAME}" \
  "${SAM_OFFICIAL_IMAGE}" run /agent.yaml

echo "Agent ${AGENT_ID} updated successfully"