#!/usr/bin/env bash
set -euo pipefail

AGENT_ID="${1:-}"
if [[ -z "${AGENT_ID}" ]]; then
  echo "Error: Agent ID required as first argument" >&2
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

debug_log "Stopping container ${CONTAINER_NAME}"
"${CONTAINER_ENGINE}" stop "${CONTAINER_NAME}"

debug_log "Removing container ${CONTAINER_NAME}"
"${CONTAINER_ENGINE}" rm "${CONTAINER_NAME}"

echo "Agent ${AGENT_ID} undeployed successfully"