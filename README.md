# Role Based Access Control (RBAC)

A robust, multi-tenant Role-Based Access Control (RBAC) system for Django applications.

---

## Overview

This package provides a comprehensive RBAC solution designed for multi-tenant SaaS applications. It allows for granular permission management at the **Module**, **SubModule**, and **API Operation** levels.

### Key Features

- **Multi-tenancy Support** — Built-in tenant isolation for users and data.
- **Granular Permissions** — Define permissions (read, create, update, delete, approve) per role.
- **Module & SubModule Management** — Organize system features into modules and submodules.
- **API-Level Security** — Block specific API operations for individual users or entire tenants.
- **RBAC Middleware** — Automatically enforces permission checks on incoming requests.
- **Tenant Middleware** — Automatically resolves and sets the current tenant context per request.

---

## Architecture

### Admin Configuration

All configuration of the RBAC system — including **roles**, **permissions**, **modules**, **submodules**, **user-role mappings**, and **tenant setup** — is currently managed through the **default Django Admin** interface.

The default admin acts as the central control layer, allowing administrators to:

- Define and manage `Modules` and `SubModules`
- Create `Permissions` scoped to specific modules and operations (read, create, update, delete, approve)
- Define `Roles` and assign `Permissions` to them via `RolePermission`
- Assign `Roles` to `Users` via `UserRole`
- Configure tenant-level API blocks via `TenantBlockedOperation`
- Configure user-level API blocks via `UserBlockedOperation`

> **Note:** A dedicated, standalone Admin Service with its own set of REST APIs and UI is planned for the future (refer lightly to `admin_service_guide.md` for architectural concepts). For now, the current Django Admin is fully capable of managing all RBAC state and should be used as the primary configuration tool.

---

## Installation

### As a Python Package (from source)

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd django_rbac_project
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install in editable mode:**
   ```bash
   pip install -e .
   ```

4. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

### Using Docker (Recommended for Deployment)

See the [Docker Setup](#docker-setup) section below.

---

## Configuration

### settings.py

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    'accounts',
    'core',
    # ...
]

AUTH_USER_MODEL = 'accounts.User'
RBAC_TENANT_MODEL = 'core.Tenant'  # Optional override
```

### Middleware

Add middlewares in this order:

```python
MIDDLEWARE = [
    # ... Django defaults ...
    'core.middleware.CurrentTenantMiddleware',   # Resolves tenant context
    # ... message/clickjacking middleware ...
    'core.services.RBACMiddleware.RBACMiddleware',    # Enforces RBAC permissions
    'core.exception_middleware.JSONExceptionMiddleware',  # Must be last
]
```

### Database (Environment-Driven)

Configure the database via environment variables (especially in Docker):

```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.environ.get('DB_NAME', 'rbac_project'),
        'USER':     os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST':     os.environ.get('DB_HOST', 'localhost'),
        'PORT':     os.environ.get('DB_PORT', '5432'),
    }
}
```

---

## Usage

### 1. Defining Modules & Permissions

Use the **Django Admin** interface (at `/admin/`) to define `Modules`, `SubModules`, and `Permissions` scoped to specific operations.

### 2. Creating Roles

Define `Roles` (e.g., *Manager*, *Sales Executive*) and attach `Permissions` via `RolePermission`.

### 3. Assigning Roles to Users

Assign users to roles using `UserRole`. A user can have multiple roles across tenants.

### 4. Checking Permissions in Code

#### In Views / Business Logic

```python
from core.utils import check_permission

if check_permission(user, 'invoice', 'read'):
    # Allow access
```

#### Via API (Automatic Enforcement)

The `RBACMiddleware` automatically checks permissions on every request based on the endpoint and HTTP method — no manual decorator needed per view.

### 5. Blocking Operations

Use `TenantBlockedOperation` to block API paths for an entire tenant, or `UserBlockedOperation` to block them for a specific user, regardless of role.

---

## Docker Setup

This project supports two independent deployment modes from the same codebase:

```
Same application
├── Personal deployment   → local Docker build (no registry needed)
└── Org deployment        → private registry (192.168.71.244:30444) + WSL
```

> See [`docs/deployment.md`](docs/deployment.md) for the full guide.

### Personal / Local (independent Docker)

```bash
cp .env.example .env   # fill in credentials
make local-up          # build from source + start
make local-logs        # follow logs
make local-down        # stop
```

### Organisation (WSL + private registry)

**One-time WSL daemon config** — allow the insecure private registry:

```bash
sudo nano /etc/docker/daemon.json
# Add: { "insecure-registries": ["192.168.71.244:30444"] }
sudo service docker restart
```

**Copy project into WSL filesystem:**

```bash
cp -r /mnt/c/Users/krish.patel/Desktop/django_rbac_project ~/rbac-admin
cd ~/rbac-admin
```

**Build & push, then deploy:**

```bash
bash scripts/build-org.sh v1.0.0   # build + push
# Set RBAC_IMAGE_TAG=v1.0.0 in .env
make org-up                        # pull + start
```

### Makefile Quick Reference

```
make help           List all targets
make local-up       Build from source + start (personal)
make org-up         Pull from registry + start (org)
make shell          Django shell in running container
make migrate        Run DB migrations
make clean          Remove stopped containers & dangling images
```

### Environment Variables (.env)

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DB_NAME` | Postgres database name |
| `DB_USER` | Postgres user |
| `DB_PASSWORD` | Postgres password |
| `DB_PORT` | Postgres port (inside container) |
| `DB_EXPOSED_PORT` | Host-side Postgres port (default `5433`) |
| `RBAC_PORT` | Host-side RBAC service port (default `8002`) |
| `RBAC_IMAGE_TAG` | Registry image tag to pull (default `latest`) |


---

## Project Structure

```
django_rbac_project/
│
├── app/                         # application source
│   ├── accounts/                # Custom User model & authentication
│   ├── core/                    # RBAC models, middleware, services, APIs
│   └── rbac_project/            # Django project settings & WSGI
│
├── docker/
│   ├── Dockerfile               # Image definition
│   ├── docker-compose.yml       # Base — shared DB + service skeleton
│   ├── docker-compose.local.yml # Personal — builds image from source
│   └── docker-compose.org.yml   # Org — pulls from private registry
│
├── scripts/
│   ├── build-local.sh           # Build image locally (no registry)
│   ├── build-org.sh             # Build + push to private registry (WSL)
│   └── run-dev.sh               # Start / stop local dev stack
│
├── docs/
│   └── deployment.md            # Full deployment guide
│
├── entrypoint.sh                # wait-for-db → migrate → collectstatic → gunicorn
├── gunicorn.conf.py             # Gunicorn worker / timeout / logging config
├── Makefile                     # Dual-env shortcuts (local-* / org-*)
├── .env.example                 # Safe-to-commit env template
├── .env                         # Runtime secrets (never commit)
├── requirements.txt             # Python dependencies
└── setup.py                     # Package distribution config
```

---

## License

[MIT License](LICENSE)
