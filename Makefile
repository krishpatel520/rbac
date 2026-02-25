# =============================================================================
# Makefile — RBAC Admin Service
#
# Dual-environment shortcuts:
#   Personal / local Docker  → make local-*
#   Organisation (WSL/registry) → make org-*
#
# Run `make help` to list all available targets.
# =============================================================================

.PHONY: help \
        local-build local-up local-down local-logs local-restart \
        org-build org-up org-down org-logs org-pull \
        shell migrate collectstatic \
        clean

# ── Compose file pairs ────────────────────────────────────────────────────────
COMPOSE_BASE    := docker/docker-compose.yml
COMPOSE_LOCAL   := docker/docker-compose.local.yml
COMPOSE_ORG     := docker/docker-compose.org.yml

DC_LOCAL  := docker compose -f $(COMPOSE_BASE) -f $(COMPOSE_LOCAL)
DC_ORG    := docker compose -f $(COMPOSE_BASE) -f $(COMPOSE_ORG)

# ── Default target ────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  RBAC Admin Service — Makefile"
	@echo "  ========================================"
	@echo ""
	@echo "  LOCAL (personal Docker)"
	@echo "    make local-build     Build image from source"
	@echo "    make local-up        Start stack (build if needed)"
	@echo "    make local-down      Stop stack (keep volumes)"
	@echo "    make local-logs      Follow service logs"
	@echo "    make local-restart   Restart rbac-service only"
	@echo ""
	@echo "  ORG (private registry + WSL)"
	@echo "    make org-build       Build & push to registry"
	@echo "    make org-pull        Pull latest image from registry"
	@echo "    make org-up          Start stack (pull image first)"
	@echo "    make org-down        Stop stack (keep volumes)"
	@echo "    make org-logs        Follow service logs"
	@echo ""
	@echo "  DJANGO MANAGEMENT"
	@echo "    make shell           Open Django shell in running container"
	@echo "    make migrate         Run database migrations"
	@echo "    make collectstatic   Collect static files"
	@echo ""
	@echo "  MAINTENANCE"
	@echo "    make clean           Remove stopped containers & dangling images"
	@echo ""

# =============================================================================
# LOCAL — personal Docker build & run
# =============================================================================

local-build:
	@echo ">>> Building local image..."
	bash scripts/build-local.sh

local-up:
	@echo ">>> Starting local stack..."
	$(DC_LOCAL) up -d --build
	@echo ">>> Service up at http://localhost:$${RBAC_PORT:-8002}"

local-down:
	@echo ">>> Stopping local stack..."
	$(DC_LOCAL) down

local-logs:
	$(DC_LOCAL) logs -f rbac-service

local-restart:
	$(DC_LOCAL) restart rbac-service

# =============================================================================
# ORG — private registry + WSL deployment
# =============================================================================

org-build:
	@echo ">>> Building and pushing org image..."
	bash scripts/build-org.sh

org-pull:
	@echo ">>> Pulling latest image from registry..."
	$(DC_ORG) pull rbac-service

org-up:
	@echo ">>> Starting org stack..."
	$(DC_ORG) up -d
	@echo ">>> Service up at http://localhost:$${RBAC_PORT:-8002}"

org-down:
	@echo ">>> Stopping org stack..."
	$(DC_ORG) down

org-logs:
	$(DC_ORG) logs -f rbac-service

# =============================================================================
# DJANGO MANAGEMENT (uses whichever stack is currently running)
# =============================================================================

shell:
	docker exec -it rbac_service python manage.py shell

migrate:
	docker exec -it rbac_service python manage.py migrate --noinput

collectstatic:
	docker exec -it rbac_service python manage.py collectstatic --noinput

# =============================================================================
# MAINTENANCE
# =============================================================================

clean:
	@echo ">>> Removing stopped containers and dangling images..."
	docker container prune -f
	docker image prune -f
	@echo ">>> Done."
