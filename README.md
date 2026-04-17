# 🛡️ MSBC RBAC (Role-Based Access Control)

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![Django 3.2+](https://img.shields.io/badge/django-3.2+-brightgreen.svg)
![Nexus Registry](https://img.shields.io/badge/registry-Nexus%20Private-orange.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-success.svg)

A centralized, enterprise-grade Role-Based Access Control (RBAC) package designed specifically for robust multi-tenant architectures and microservices. 

> **⚠️ IMPORTANT ORGANIZATIONAL CONTEXT**
> This RBAC core system has been officially built, packaged, and **uploaded to the company's private package registry (Nexus Server)**. It is actively consumed as a core dependency across many different applications and microservices to ensure unified authentication, authorization, and tenant isolation policies.

---

## 🌟 Core Features

- **Multi-Tenant Architecture**: Deep database and request isolation layer.
- **Granular API Security**: Route-based and HTTP method-based control for `read`, `create`, `update`, `delete`, and `approve`.
- **Module & SubModule Hierarchy**: Organize application components consistently across the board.
- **Middleware-Driven Safety**: `RBACMiddleware` and `CurrentTenantMiddleware` intercept, validate, and isolate context explicitly before view execution.
- **Microservices Ready**: Easily installable as a `.whl` or `tar.gz` package via Pip. It is decoupled from domain logic to be securely deployed on various independent Django services.
- **Dynamic API Blocking**: Supports full tenant-level API path blocking (`TenantBlockedOperation`) and individualized edge-case rule setting (`UserBlockedOperation`).

---

## 🚀 Detailed Integration Flow for Microservices

Because this project is consumed as a centralized package by other microservices (like the Auth Service, User Service, etc.), follow this exact flow to integrate RBAC into any new Django service.

### Step 1: Install the Package from Nexus
Point your package manager to the internal Nexus repository and install `msbc-rbac`:
```bash
# Connect to our private registry and install the core framework
pip install msbc-rbac --extra-index-url https://nexus.company.local/repository/pypi/simple
```

### Step 2: Configure `settings.py`

Register the RBAC apps and configure your model mappings.

```python
INSTALLED_APPS = [
    # ... your native apps
    'rest_framework',
    'rest_framework.authtoken',
    
    # 🔌 Inject MSBC RBAC Modules
    'msbc_rbac.accounts',
    'msbc_rbac.core',
]

# Map your tenant and auth models to ensure the RBAC system binds correctly
AUTH_USER_MODEL = 'accounts.User'
RBAC_TENANT_MODEL = 'core.Tenant'  # Maps context to package architecture
```

### Step 3: Add Critical Middlewares
**Order is incredibly important.** Tenant resolution must execute prior to RBAC permission evaluations.

```python
MIDDLEWARE = [
    # ... standard django core middlewares ...
    
    # 1. Resolves tenant context from headers/token
    'msbc_rbac.core.middleware.CurrentTenantMiddleware',  
    
    # 2. Enforces RBAC permissions based on DB policies
    'msbc_rbac.core.services.RBACMiddleware.RBACMiddleware', 
    
    # 3. Ensures JSON error adherence on failure
    'msbc_rbac.core.exception_middleware.JSONExceptionMiddleware', 
]
```

### Step 4: Run Package Migrations
Once bound, you must apply the RBAC database architectures into the microservice's database schema:
```bash
python manage.py migrate
```

### Step 5: Initialize the API & Permission State
Depending on the service, you will inject initial tenants, baseline roles, and sync operational scopes (e.g. `api_sync_db_operation`) so the RBAC database mapping recognizes the microservices' endpoints.

---

## ⚙️ Operations & Usage Flow

Once integrated, developers and administrators leverage the following operational flow to manage security:

### 1. Defining Modules & Permissions
Administrators use the **Django Admin** interface (`/admin/`) on the centralized MSBC Admin Gateway to define `Modules`, `SubModules`, and `Permissions` scoped to operations (e.g., read, update, delete).

### 2. Creating Roles
Administrators define cross-system `Roles` (e.g., *Manager*, *Sales Executive*) and structurally attach `Permissions` via `RolePermission`.

### 3. Assigning Roles to Users
A user identity is mapped to a role strictly using `UserRole`. Users can securely possess multiple varying roles across disparate tenants within the SaaS.

### 4. Automatic API Enforcement 
The `RBACMiddleware` automatically validates identity vs. permissions on strictly typed endpoints (`GET`, `POST`, `PUT`, `DELETE`). 
**No manual decorators per view are required anymore.** The service inherently knows if a User in a Tenant context has `write` access based purely on the `settings.py` binding flow.

### 5. Manual Permission Handling (Code Level)
If you require code-level conditional checking (for rendering templates or executing complex secondary logic):
```python
from msbc_rbac.core.utils import check_permission

if check_permission(user, 'reporting', 'read'):
    # Generate confidential payload
```

### 6. Dynamic Operation Blocking
Edge cases exist where standard role models fail. The system handles this via:
- `TenantBlockedOperation`: Blankets API path denial to an entire tenant regardless of user roles.
- `UserBlockedOperation`: Granularly blocks an API explicitly for a specific user identity.

---

## 🐳 Dockerized Internal Environments

Both the internal API gateway/administration applications and connected services leverage isolated configurations.

**Personal System Execution**
```bash
cp .env.example .env
make local-up
```

**Standard Production (Org Deployment via WSL)**
Ensures WSL nodes interact with our private registry components securely.
```bash
sudo nano /etc/docker/daemon.json
# Ensure insecure-registries handles corporate internal network tags
bash scripts/build-org.sh v1.0.0
make org-up
```

---

*Property of MSBC Group Core Engineering.*
