from core.services.permission_api_resolver import has_permission, get_user_permissions, user_api_blocked, \
    tenant_api_disabled, resolve_api_operation


class RBACMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        tenant = getattr(user, 'tenant', None)

        if not user or not user.is_authenticated:
            return self.get_response(request)

        operation = resolve_api_operation(request)
        if not operation:
            raise PermissionError("API not registered")

        # Platform-level disable
        if not operation.is_enabled:
            raise PermissionError("API disabled")

        # Tenant-level API block
        if tenant_api_disabled(tenant, operation):
            raise PermissionError("API disabled for tenant")

        # User-level API block (deny wins)
        if user_api_blocked(tenant, user, operation):
            raise PermissionError("API blocked for user")

        permissions = get_user_permissions(tenant, user)

        # Module-level permission
        if has_permission(
            permissions,
            module=operation.module,
            submodule=None,
            action=operation.action
        ):
            return self.get_response(request)

        # Submodule fallback
        if operation.submodule and has_permission(
            permissions,
            module=operation.module,
            submodule=operation.submodule,
            action=operation.action
        ):
            return self.get_response(request)

        raise PermissionError("Permission denied")
