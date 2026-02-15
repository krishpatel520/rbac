from datetime import date

from core.models import TenantModule
from core.rbac.constants import HTTP_METHOD_ACTION_MAP
from core.services.permission_api_resolver import (
    has_permission,
    get_user_permissions,
    user_api_blocked,
    tenant_api_disabled,
    resolve_api_operation,
)


class RBACMiddleware:
    """
    Enforces RBAC + Tenant Subscription + API Overrides.

    Priority Order (Deny Wins):
    1. Infrastructure bypass
    2. Authentication handled elsewhere
    3. API must be registered
    4. Platform-level disable
    5. Tenant subscription module check
    6. Tenant API override block
    7. User API block (highest priority)
    8. Role → Permission check
    9. Default deny
    """

    # Paths that should NEVER be RBAC protected
    BYPASS_PATH_PREFIXES = (
        "/admin/",
        "/accounts/",
        "/dashboard/",
        "/static/",
        "/media/",
        "/favicon.ico",
        "/api/schema/",
        "/api/docs/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # ─────────────────────────────
        # 1️⃣ Infrastructure bypass
        # ─────────────────────────────
        # Django admin, static files, docs etc. should never be blocked by RBAC
        for prefix in self.BYPASS_PATH_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        # Get authenticated user
        user = request.user

        # ─────────────────────────────
        # 2️⃣ Anonymous users bypass
        # ─────────────────────────────
        # Authentication is handled separately (JWT / Session Middleware)
        if not user or not user.is_authenticated:
            return self.get_response(request)

        # Tenant attached to user (multi-tenant SaaS)
        tenant = getattr(user, "tenant", None)

        # ─────────────────────────────
        # 3️⃣ Resolve API operation
        # ─────────────────────────────
        # Find ApiOperation based on request path + method
        operation = resolve_api_operation(request)
        if not operation:
            # Security: deny unknown APIs
            raise PermissionError("API not registered")

        # ─────────────────────────────
        # 4️⃣ Platform-level API disable
        # ─────────────────────────────
        # Super admin can globally disable API for maintenance/security
        if not operation.is_enabled:
            raise PermissionError("API disabled globally")

        # ─────────────────────────────
        # 5️⃣ Tenant module subscription check
        # ─────────────────────────────
        # Tenant must have purchased/enabled this module/submodule
        if tenant:
            tm = TenantModule.objects.filter(
                tenant=tenant,
                module=operation.endpoint.module,
                submodule=operation.endpoint.submodule,
            ).first()

            # Tenant never subscribed to module
            if not tm:
                raise PermissionError("Tenant not subscribed to module")

            # Module disabled manually for tenant
            if not tm.is_enabled:
                raise PermissionError("Module disabled for tenant")

            # Subscription expired
            if tm.expiration_date and tm.expiration_date < date.today():
                raise PermissionError("Tenant subscription expired")

        # ─────────────────────────────
        # 6️⃣ Tenant-level API override
        # ─────────────────────────────
        # Tenant admin can disable specific API even if module is enabled
        if tenant_api_disabled(tenant, operation):
            raise PermissionError("API disabled for tenant")

        # ─────────────────────────────
        # 7️⃣ User-level explicit API block
        # ─────────────────────────────
        # Highest priority deny (even if role allows)
        if user_api_blocked(tenant, user, operation):
            raise PermissionError("API blocked for user")

        # ─────────────────────────────
        # 8️⃣ Resolve permission action code
        # ─────────────────────────────
        # If ApiOperation has custom permission_code use it,
        # otherwise derive from HTTP method (GET → view, POST → create, etc.)
        action_code = (
            operation.permission_code
            or HTTP_METHOD_ACTION_MAP.get(request.method.upper())
        )

        if not action_code:
            raise PermissionError("Unknown action mapping")

        # ─────────────────────────────
        # 9️⃣ Fetch user permissions
        # ─────────────────────────────
        # This returns set of tuples:
        # (module_code, submodule_code | None, permission_code)
        permissions = get_user_permissions(tenant, user)

        # Debug logs (remove in production)
        print("DEBUG permissions:", permissions)
        print(
            f"DEBUG checking → module={operation.endpoint.module.code}, "
            f"submodule={operation.endpoint.submodule.code if operation.endpoint.submodule else None}, "
            f"action={action_code}"
        )

        # ─────────────────────────────
        # 🔟 Module-level permission check
        # ─────────────────────────────
        # If tenant granted permission at module level → allow all submodules
        if has_permission(
            permissions,
            module=operation.endpoint.module,
            submodule=None,
            action=action_code,
        ):
            return self.get_response(request)

        # ─────────────────────────────
        # 1️⃣1️⃣ Submodule-level permission fallback
        # ─────────────────────────────
        # If module-level not granted, check submodule-specific permission
        if operation.endpoint.submodule and has_permission(
            permissions,
            module=operation.endpoint.module,
            submodule=operation.endpoint.submodule,
            action=action_code,
        ):
            return self.get_response(request)

        # ─────────────────────────────
        # 1️⃣2️⃣ Final deny (default deny policy)
        # ─────────────────────────────
        raise PermissionError("Permission denied")
