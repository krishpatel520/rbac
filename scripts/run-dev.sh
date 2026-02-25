#!/bin/bash
# =============================================================================
# scripts/run-dev.sh — Start RBAC Admin Service for local development
#
# Spins up PostgreSQL and the RBAC service using the local compose override.
# Builds the image fresh if it doesn't exist or --build is passed.
#
# Usage:
#   chmod +x scripts/run-dev.sh
#   ./scripts/run-dev.sh           → start (build if needed)
#   ./scripts/run-dev.sh --build   → force rebuild, then start
#   ./scripts/run-dev.sh --down    → stop and remove containers
#
# Or use the Makefile:
#   make local-up
#   make local-down
# =============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

COMPOSE_BASE="${ROOT}/docker/docker-compose.yml"
COMPOSE_LOCAL="${ROOT}/docker/docker-compose.local.yml"

MODE="${1:---up}"

case "${MODE}" in
  --down)
    echo ">>> Stopping RBAC dev stack..."
    docker compose \
      -f "${COMPOSE_BASE}" \
      -f "${COMPOSE_LOCAL}" \
      down
    echo ">>> Stack stopped (volumes preserved)."
    ;;

  --build)
    echo ">>> Building and starting RBAC dev stack (forced rebuild)..."
    docker compose \
      -f "${COMPOSE_BASE}" \
      -f "${COMPOSE_LOCAL}" \
      up -d --build
    echo ""
    echo ">>> Service is up. Logs:"
    docker compose \
      -f "${COMPOSE_BASE}" \
      -f "${COMPOSE_LOCAL}" \
      logs --tail=30 rbac-service
    ;;

  *)
    echo ">>> Starting RBAC dev stack..."
    docker compose \
      -f "${COMPOSE_BASE}" \
      -f "${COMPOSE_LOCAL}" \
      up -d
    echo ""
    echo ">>> Service is up at http://localhost:8002"
    echo ">>> Logs: docker compose -f docker/docker-compose.yml -f docker/docker-compose.local.yml logs -f"
    ;;
esac
