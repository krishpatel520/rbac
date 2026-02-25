#!/bin/bash
# =============================================================================
# scripts/build-org.sh — Build and push the RBAC Admin image to the private
# organisation registry (run from inside WSL)
#
# Usage:
#   chmod +x scripts/build-org.sh
#   ./scripts/build-org.sh [TAG]
#
# Examples:
#   ./scripts/build-org.sh           → tags as latest
#   ./scripts/build-org.sh v1.0.0   → tags as v1.0.0
#
# Requires:
#   - Docker running inside WSL
#   - Network access to ORG_REGISTRY (default: 192.168.71.244:30444)
# =============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── Configuration ────────────────────────────────────────────────────────────
REGISTRY="${ORG_REGISTRY:-192.168.71.244:30444}"
IMAGE_NAME="rbac-admin"
TAG="${1:-latest}"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"
REGISTRY_USER="${ORG_REGISTRY_USER:-Hiren}"

echo "=============================================="
echo "  RBAC Admin — Org Build & Push"
echo "  Registry : ${REGISTRY}"
echo "  Image    : ${FULL_IMAGE}"
echo "=============================================="

# ── Step 1: Login to private registry ────────────────────────────────────────
echo ""
echo ">>> [1/4] Logging in to registry ${REGISTRY}..."
docker login -u "${REGISTRY_USER}" "http://${REGISTRY}/"
echo ">>> Login successful"

# ── Step 2: Build image ───────────────────────────────────────────────────────
echo ""
echo ">>> [2/4] Building image: ${FULL_IMAGE}"
docker build \
    --no-cache \
    --label "build.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --label "build.version=${TAG}" \
    --label "build.environment=org" \
    -f "${ROOT}/docker/Dockerfile" \
    -t "${FULL_IMAGE}" \
    "${ROOT}"
echo ">>> Build complete"

# ── Step 3: Verify the image exists locally ───────────────────────────────────
echo ""
echo ">>> [3/4] Verifying image..."
docker images "${REGISTRY}/${IMAGE_NAME}"

# ── Step 4: Push to registry ──────────────────────────────────────────────────
echo ""
echo ">>> [4/4] Pushing ${FULL_IMAGE} to registry..."
docker push "${FULL_IMAGE}"

echo ""
echo "=============================================="
echo "  Done! Image pushed successfully."
echo "  ${FULL_IMAGE}"
echo "  Deploy with: make org-up"
echo "=============================================="
