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

## Docker Setup (WSL + Private Registry)

The RBAC Admin image is built **inside WSL** and pushed to the organisation's private registry at `192.168.71.244:30444`.

> **Do not build from `/mnt/c`.** Always copy the project into the WSL filesystem first.

### 1. One-time WSL Daemon Configuration

The private registry runs over plain HTTP (not HTTPS). Tell Docker to trust it:

```bash
# Create or edit the daemon config
sudo mkdir -p /etc/docker
sudo nano /etc/docker/daemon.json
```

Paste the following and save:

```json
{
  "insecure-registries": ["192.168.71.244:30444"]
}
```

Restart the Docker daemon:

```bash
sudo dockerd &
# or, if using a service:
sudo service docker restart
```

---

### 2. Copy Project into WSL Filesystem

```bash
# Inside WSL — run once (or after major changes)
cp -r /mnt/c/Users/krish.patel/Desktop/django_rbac_project ~/rbac-admin
cd ~/rbac-admin
```

---

### 3. Build & Push (via script)

```bash
# Make the script executable (first time only)
chmod +x build_push.sh

# Build and push with 'latest' tag
./build_push.sh

# Build and push with a specific tag
./build_push.sh v1.0.0
```

The script will:
1. Log in to `192.168.71.244:30444` as user `Hiren`
2. Build the image tagged `192.168.71.244:30444/rbac-admin:<tag>`
3. Print the local image list
4. Push to the private registry

---

### 4. Manual Commands (step by step)

```bash
# Login
docker login -u Hiren http://192.168.71.244:30444/
# Enter password: Admin@1234

# Build
docker build -t 192.168.71.244:30444/rbac-admin:latest .

# Verify local image
docker images

# Push
docker push 192.168.71.244:30444/rbac-admin:latest
```

---

### 5. Run the Stack (WSL)

The `docker-compose.yml` **pulls** the image from the registry (no local build).

```bash
# Set the tag in .env (edit DB_PASSWORD, SECRET_KEY etc. first)
nano .env
# Set: RBAC_IMAGE_TAG=latest (or the tag you pushed)

# Pull latest image from registry + start all containers
docker-compose pull rbac-service
docker-compose up -d

# Check logs
docker-compose logs -f
docker logs rbac_service
docker logs rbac_db

# Stop (keeps DB volume)
docker-compose down

# Stop + wipe DB data
docker-compose down -v
```

---

### 6. If Docker Stops Working

```bash
sudo dockerd &
```

---

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
├── accounts/               # Custom User model & authentication
├── core/
│   ├── exceptions.py       # RBACPermissionDenied (typed violation codes)
│   ├── models.py           # Tenant, Role, Permission, UserRole, RolePermission, etc.
│   ├── middleware.py        # CurrentTenantMiddleware
│   ├── exception_middleware.py   # JSON exception catcher
│   ├── drf_exception_handler.py  # DRF JSON error handler
│   ├── services/
│   │   └── RBACMiddleware.py     # RBAC enforcement middleware
│   ├── api/                # DRF views & serializers
│   └── management/         # Custom management commands
├── rbac_project/           # Django project settings & WSGI
├── Dockerfile              # Image definition
├── docker-compose.yml      # Multi-container stack (pulls from private registry)
├── entrypoint.sh           # Container startup: wait-for-db → migrate → collectstatic → start
├── build_push.sh           # WSL script: login → build → push to private registry
├── gunicorn.conf.py        # Gunicorn worker/timeout/logging config
├── .env                    # Runtime secrets (never commit)
├── requirements.txt        # Python dependencies
└── setup.py                # Package distribution config
```

---

## License

[MIT License](LICENSE)
