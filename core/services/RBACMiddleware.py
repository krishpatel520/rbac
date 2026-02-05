from core.services.permission_api_resolver import (
    has_permission,
    get_user_permissions,
    user_api_blocked,
    tenant_api_disabled,
    resolve_api_operation,
)


from datetime import date
from core.models import TenantModule

class RBACMiddleware:
    """
    Enforces RBAC + ABAC on registered API endpoints.

    Design principles:
    - Infrastructure routes (admin, static, media) are NEVER RBAC-protected
    - Unauthenticated users pass through (auth handled elsewhere)
    - Deny-by-default for registered APIs
    - Explicit deny always wins
    """

    BYPASS_PATH_PREFIXES = (
        "/admin/",
        "/accounts/",
        "/dashboard/",
        "/static/",
        "/media/",
        "/favicon.ico",
        "/api/schema/",  # OpenAPI schema endpoint
        "/api/docs/",    # Swagger UI
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        
        print("path", path)

        # ─────────────────────────────
        # 1️⃣ Infrastructure bypass
        # ─────────────────────────────
        for prefix in self.BYPASS_PATH_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        user = request.user
        print("request", request.headers)
        
        print("user", user)

        # ─────────────────────────────
        # 2️⃣ Anonymous users bypass
        # (authentication handled separately)
        # ─────────────────────────────
        if not user or not user.is_authenticated:
            return self.get_response(request)

        tenant = getattr(user, "tenant", None)

        # ─────────────────────────────
        # 3️⃣ Resolve API operation
        # ─────────────────────────────
        operation = resolve_api_operation(request)

        if not operation:
            raise PermissionError("API not registered")

        # ─────────────────────────────
        # 4️⃣ Platform-level API disable
        # ─────────────────────────────
        if not operation.is_enabled:
            raise PermissionError("API disabled")

        # ─────────────────────────────
        # 4.5️⃣ Tenant module subscription check
        # ─────────────────────────────
        if tenant:
            tm = TenantModule.objects.filter(
                tenant=tenant,
                module=operation.endpoint.module,
                submodule=operation.endpoint.submodule,
            ).first()

            if not tm:
                raise PermissionError("Tenant not subscribed to this module")

            if not tm.is_enabled:
                raise PermissionError("Module/Submodule disabled for tenant")

            if tm.expiration_date and tm.expiration_date < date.today():
                raise PermissionError("Tenant subscription expired")

        # ─────────────────────────────
        # 5️⃣ Tenant-level API override
        # ─────────────────────────────
        if tenant_api_disabled(tenant, operation):
            raise PermissionError("API disabled for tenant")

        # ─────────────────────────────
        # 6️⃣ User-level explicit deny
        # (deny always wins)
        # ─────────────────────────────
        if user_api_blocked(tenant, user, operation):
            raise PermissionError("API blocked for user")

        # ─────────────────────────────
        # 7️⃣ Permission resolution
        # ─────────────────────────────
        permissions = get_user_permissions(tenant, user)
        
        print(f"DEBUG: User permissions: {permissions}")
        print(f"DEBUG: Checking module={operation.endpoint.module.code}, submodule={operation.endpoint.submodule.code if operation.endpoint.submodule else None}, action={operation.action.code}")

        # Module-level permission
        if has_permission(
            permissions=permissions,
            module=operation.endpoint.module,
            submodule=None,
            action=operation.action,
        ):
            print("DEBUG: ALLOWED via module-level permission")
            return self.get_response(request)

        # Submodule-level permission (fallback)
        if (
            operation.endpoint.submodule
            and has_permission(
                permissions=permissions,
                module=operation.endpoint.module,
                submodule=operation.endpoint.submodule,
                action=operation.action,
            )
        ):
            print("DEBUG: ALLOWED via submodule-level permission")
            return self.get_response(request)

        # ─────────────────────────────
        # 8️⃣ Final deny
        # ─────────────────────────────
        print("DEBUG: DENIED - No matching permission found")
        raise PermissionError("Permission denied")

