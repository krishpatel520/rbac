# Role Based Access Control (RBAC)

A robust, multi-tenant Role-Based Access Control (RBAC) system for Django applications.

## Overview

This project provides a comprehensive RBAC solution designed for multi-tenant SaaS applications. It allows for granular permission management at the Module, SubModule, and API Operation levels.

### Key Features
- **Multi-tenancy Support**: Built-in tenant isolation for users and data.
- **Granular Permissions**: Define permissions (read, create, update, delete, approve) per role.
- **Module & SubModule Management**: Organize system features into modules and submodules.
- **API-Level Security**: Block specific API operations for individual users or entire tenants.
- **Custom Middleware**: Automatically resolves and sets the current tenant context.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd django_rbac_project
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r req.txt
   ```

4. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

## Configuration

### Settings

Ensure your `settings.py` includes the necessary configurations:

```python
# settings.py

INSTALLED_APPS = [
    # ...
    'core',
    'accounts',
    # ...
]

AUTH_USER_MODEL = 'accounts.User'
RBAC_TENANT_MODEL = 'core.Tenant'  # Optional override
```

### Middleware

Add the tenant middleware to your `MIDDLEWARE` setting:

```python
MIDDLEWARE = [
    # ...
    'core.middleware.CurrentTenantMiddleware',
    # ...
]
```

## Usage

### 1. Defining Modules and Permissions
Use the Django Admin to define your system's `Modules` and `SubModules`. Create `Permissions` linked to these modules.

### 2. Creating Roles
Define `Roles` (e.g., "Manager", "Sales Executive") and assign `Permissions` to them via the `RolePermission` model.

### 3. Assigning Roles to Users
Assign users to roles using the `UserRole` model.

### 4. Checking Permissions in Code

#### In Views
Use the provided helpers or decorators to check permissions:

```python
from core.utils import check_permission

if check_permission(user, 'invoice', 'read'):
    # Allow access
```

#### In API Views
The system integrates with DRF to automatically check permissions based on the API endpoint and method if configured.

## Project Structure

- **accounts/**: Custom User model and authentication views.
- **core/**: Core RBAC logic, models (Tenant, Role, Permission), and middleware.
- **rbac_project/**: Project settings and configuration.

## License

[MIT License](LICENSE)
