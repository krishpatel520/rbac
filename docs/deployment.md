# Deployment Guide

RBAC Admin Service supports two independent deployment modes from the same codebase.

---

## Architecture Overview

```
Same application
├── Personal deployment   → local Docker build (no registry)
└── Org deployment        → private registry + WSL
```

All shared service definitions live in `docker/docker-compose.yml`.  
Environment-specific concerns are isolated in override files:

| File | Purpose |
|------|---------|
| `docker/docker-compose.yml` | Base — shared DB + service skeleton |
| `docker/docker-compose.local.yml` | Personal — builds image from source |
| `docker/docker-compose.org.yml` | Org — pulls image from private registry |

---

## Prerequisites

- Docker Desktop (local) **or** Docker in WSL (org)
- `.env` file created from `.env.example`:
  ```bash
  cp .env.example .env
  # then edit .env with real values
  ```

---

## Personal / Local Deployment

No registry account needed. Builds directly from source.

```bash
# Build image
make local-build
# OR: bash scripts/build-local.sh

# Start stack
make local-up

# View logs
make local-logs

# Stop
make local-down
```

Service runs at: **http://localhost:8002**

---

## Organisation Deployment (WSL + Private Registry)

Requires WSL with Docker and access to `192.168.71.244:30444`.

### Step 1 — Build & push (from WSL)

```bash
bash scripts/build-org.sh v1.0.0
# OR: make org-build
```

This will:
1. Login to the private registry
2. Build the image from source
3. Push `192.168.71.244:30444/rbac-admin:<tag>` to the registry

### Step 2 — Deploy

```bash
# Set the correct tag in .env
echo "RBAC_IMAGE_TAG=v1.0.0" >> .env

make org-up
# OR: docker compose -f docker/docker-compose.yml -f docker/docker-compose.org.yml up -d
```

---

## Environment Variables

See [`.env.example`](../.env.example) for the full list.

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | — |
| `DB_NAME` | PostgreSQL database name | `rbac_project` |
| `DB_USER` | PostgreSQL user | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | — |
| `DB_EXPOSED_PORT` | Host-side Postgres port | `5433` |
| `RBAC_PORT` | Host-side service port | `8002` |
| `RBAC_IMAGE_TAG` | Image tag to pull (org only) | `latest` |
| `ORG_REGISTRY` | Private registry address | `192.168.71.244:30444` |
| `ORG_REGISTRY_USER` | Registry login username | `Hiren` |

---

## Makefile Reference

```
make help           Show all targets
make local-up       Start personal stack
make local-down     Stop personal stack
make org-up         Start org stack
make org-down       Stop org stack
make shell          Django shell in running container
make migrate        Run DB migrations
make clean          Remove stopped containers & dangling images
```

---

## Compose File Reference

```
docker/
├── docker-compose.yml        ← base (always include first)
├── docker-compose.local.yml  ← personal override (build from source)
└── docker-compose.org.yml    ← org override (pull from registry)
```

Always pair the base with exactly one override:

```bash
# Personal
docker compose -f docker/docker-compose.yml -f docker/docker-compose.local.yml [cmd]

# Org
docker compose -f docker/docker-compose.yml -f docker/docker-compose.org.yml [cmd]
```
