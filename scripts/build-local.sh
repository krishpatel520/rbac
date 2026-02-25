#!/bin/bash
# =============================================================================
# scripts/build-local.sh — Build the RBAC Admin image locally
#
# Usage:
#   chmod +x scripts/build-local.sh
#   ./scripts/build-local.sh [TAG]
#
# Examples:
#   ./scripts/build-local.sh          → tags as rbac-admin:local
#   ./scripts/build-local.sh v1.2.0   → tags as rbac-admin:v1.2.0
#
# This script builds the Docker image from source without pushing to any
# registry. Intended for personal / local development.
# =============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${1:-local}"
IMAGE="rbac-admin:${TAG}"

echo "=============================================="
echo "  RBAC Admin — Local Docker Build"
echo "  Image : ${IMAGE}"
echo "=============================================="

echo ""
echo ">>> [1/2] Building image from source..."
docker build \
    --no-cache \
    --label "build.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --label "build.version=${TAG}" \
    --label "build.environment=local" \
    -f "${ROOT}/docker/Dockerfile" \
    -t "${IMAGE}" \
    "${ROOT}"

echo ">>> Build complete"

echo ""
echo ">>> [2/2] Verifying image..."
docker images rbac-admin

echo ""
echo "=============================================="
echo "  Done! Image built: ${IMAGE}"
echo "  Start with: make local-up"
echo "=============================================="
