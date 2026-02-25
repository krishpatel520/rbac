#!/bin/bash
# =============================================================================
# build_push.sh — Build and push the RBAC Admin image to the private registry
#
# Usage (inside WSL):
#   chmod +x build_push.sh
#   ./build_push.sh [TAG]
#
# Examples:
#   ./build_push.sh           → uses "latest" as tag
#   ./build_push.sh v1.0.0    → tags as v1.0.0
# =============================================================================

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
REGISTRY="192.168.71.244:30444"
IMAGE_NAME="rbac-admin"
TAG="${1:-latest}"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "========================================"
echo "  RBAC Admin — Docker Build & Push"
echo "  Image : ${FULL_IMAGE}"
echo "========================================"

# ── Step 1: Login to private registry ─────────────────────────────────────────
echo ""
echo ">>> [1/4] Logging in to registry ${REGISTRY}..."
docker login -u Hiren "http://${REGISTRY}/"
echo ">>> Login successful"

# ── Step 2: Build image ────────────────────────────────────────────────────────
echo ""
echo ">>> [2/4] Building image: ${FULL_IMAGE}"
docker build \
    --no-cache \
    --label "build.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --label "build.version=${TAG}" \
    -t "${FULL_IMAGE}" \
    .
echo ">>> Build complete"

# ── Step 3: Verify the image exists locally ────────────────────────────────────
echo ""
echo ">>> [3/4] Verifying image..."
docker images "${REGISTRY}/${IMAGE_NAME}"

# ── Step 4: Push to registry ───────────────────────────────────────────────────
echo ""
echo ">>> [4/4] Pushing ${FULL_IMAGE} to registry..."
docker push "${FULL_IMAGE}"

echo ""
echo "========================================"
echo "  Done! Image pushed successfully."
echo "  ${FULL_IMAGE}"
echo "========================================"
