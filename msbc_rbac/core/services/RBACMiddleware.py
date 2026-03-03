"""
RBAC Enforcement Middleware.

Priority Order (Deny Wins):
 1. Infrastructure bypass  (admin, static, docs)
 2. Anonymous users pass through  (auth handled elsewhere)
 3. API must be registered in ApiOperation table
 4. Platform-level API disable
 5. Tenant subscription module check
 6. Tenant-level API override block
 7. User-level explicit API block  (highest-priority deny)
 8. Role → Permission check  (module-level, then submodule-level)
 9. Default deny
"""
from datetime import date
from django.conf import settings

from msbc_rbac.core.models import TenantModule
from django.http import JsonResponse
from msbc_rbac.core.rbac.constants import HTTP_METHOD_ACTION_MAP
from msbc_rbac.core.services.permission_api_resolver import (
    has_permission,
    get_user_permissions,
    user_api_blocked,
    tenant_api_disabled,
    resolve_api_operation,
)




class RBACMiddleware:
    """
    Enforces RBAC + Tenant Subscription + API Overrides.

    All denials raise ``RBACPermissionDenied`` which carries both a
    machine-readable ``violation_type`` and a human-readable ``detail``
    message.  The ``JSONExceptionMiddleware`` converts these into
    structured 403 JSON responses.
    """

    # Paths that should NEVER be RBAC-protected
    BYPASS_PATH_PREFIXES = settings.BYPASS_PATH_PREFIXES

    print("BYPASS_PATH_PREFIXES >>>>> ",BYPASS_PATH_PREFIXES)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # ─────────────────────────────────────────────────────
        # 1. Infrastructure bypass
        # ─────────────────────────────────────────────────────
        for prefix in self.BYPASS_PATH_PREFIXES:
            path = path.rstrip("/") or "/"
            prefix = prefix.rstrip("/") or "/"
            path = path.rstrip("/") or "/"
            if path == prefix or path.startswith(prefix + "/"):
                return self.get_response(request)

        user = request.user

        # ─────────────────────────────────────────────────────
        # 2. Anonymous users bypass  (auth handled separately)
        # ─────────────────────────────────────────────────────
        if not user or not user.is_authenticated:
            return self.get_response(request)

        tenant = getattr(user, "tenant", None)

        # ─────────────────────────────────────────────────────
        # 3. API must be registered
        # ─────────────────────────────────────────────────────
        operation = resolve_api_operation(request)
        if not operation:
            # raise RBACPermissionDenied(
            #     violation_type=RBACPermissionDenied.API_NOT_REGISTERED,
            #     detail=(
            #         f"The API endpoint '{request.method} {path}' is not registered "
            #         "in the system. Access is denied."
            #     ),
            # )
            return JsonResponse(
                {"data": {}, "success": False,
                 "error": "User is not authorized",
                 "message": "User is not authorized"},
                status=401
            )

        # ─────────────────────────────────────────────────────
        # 4. Platform-level API disable
        # ─────────────────────────────────────────────────────
        if not operation.is_enabled:
            # raise RBACPermissionDenied(
            #     violation_type=RBACPermissionDenied.API_DISABLED_GLOBALLY,
            #     detail=(
            #         f"The API endpoint '{request.method} {path}' has been disabled "
            #         "globally by the platform administrator."
            #     ),
            # )
            return JsonResponse(
                {"data": {}, "success": False,
                 "error": "User is not authorized",
                 "message": "User is not authorized"},
                status=401
            )

        # ─────────────────────────────────────────────────────
        # 5. Tenant module subscription check
        # ─────────────────────────────────────────────────────
        if tenant:
            tm = TenantModule.objects.filter(
                tenant=tenant,
                module=operation.endpoint.module,
                submodule=operation.endpoint.submodule,
            ).first()

            if not tm:
                # raise RBACPermissionDenied(
                #     violation_type=RBACPermissionDenied.TENANT_NOT_SUBSCRIBED,
                #     detail=(
                #         f"Tenant '{tenant}' does not have an active subscription "
                #         f"to the module '{operation.endpoint.module}'. Access is denied."
                #     ),
                # )
                return JsonResponse(
                    {"data": {}, "success": False,
                     "error": "User is not authorized",
                     "message": "User is not authorized"},
                    status=401
                )

            if not tm.is_enabled:
                # raise RBACPermissionDenied(
                #     violation_type=RBACPermissionDenied.MODULE_DISABLED,
                #     detail=(
                #         f"Module '{operation.endpoint.module}' has been disabled "
                #         f"for tenant '{tenant}' by the tenant administrator."
                #     ),
                # )
                return JsonResponse(
                    {"data": {}, "success": False,
                     "error": "User is not authorized",
                     "message": "User is not authorized"},
                    status=401
                )

            if tm.expiration_date and tm.expiration_date < date.today():
                # raise RBACPermissionDenied(
                #     violation_type=RBACPermissionDenied.SUBSCRIPTION_EXPIRED,
                #     detail=(
                #         f"Tenant '{tenant}' subscription for module "
                #         f"'{operation.endpoint.module}' expired on {tm.expiration_date}."
                #     ),
                # )
                return JsonResponse(
                    {"data": {}, "success": False,
                     "error": "User is not authorized",
                     "message": "User is not authorized"},
                    status=401
                )

        # ─────────────────────────────────────────────────────
        # 6. Tenant-level API override
        # ─────────────────────────────────────────────────────
        if tenant_api_disabled(tenant, operation):
            # raise RBACPermissionDenied(
            #     violation_type=RBACPermissionDenied.API_DISABLED_FOR_TENANT,
            #     detail=(
            #         f"The API endpoint '{request.method} {path}' has been "
            #         f"disabled by the administrator for tenant '{tenant}'."
            #     ),
            # )
            return JsonResponse(
                {"data": {}, "success": False,
                 "error": "User is not authorized",
                 "message": "User is not authorized"},
                status=401
            )

        # ─────────────────────────────────────────────────────
        # 7. User-level explicit API block  (highest-priority deny)
        # ─────────────────────────────────────────────────────
        if user_api_blocked(tenant, user, operation):
            # raise RBACPermissionDenied(
            #     violation_type=RBACPermissionDenied.API_BLOCKED_FOR_USER,
            #     detail=(
            #         f"User '{user}' has been explicitly blocked from accessing "
            #         f"'{request.method} {path}'."
            #     ),
            # )
            return JsonResponse(
                {"data": {}, "success": False,
                 "error": "User is not authorized",
                 "message": "User is not authorized"},
                status=401
            )

        # ─────────────────────────────────────────────────────
        # 8. Resolve permission action code
        # ─────────────────────────────────────────────────────
        action_code = (
            operation.permission_code
            or HTTP_METHOD_ACTION_MAP.get(request.method.upper())
        )

        if not action_code:
            # raise RBACPermissionDenied(
            #     violation_type=RBACPermissionDenied.UNKNOWN_ACTION,
            #     detail=(
            #         f"Cannot map HTTP method '{request.method}' to a permission "
            #         "action code. The endpoint may be misconfigured."
            #     ),
            # )
            return JsonResponse(
                {"data": {}, "success": False,
                 "error": "User is not authorized",
                 "message": "User is not authorized"},
                status=401
            )

        # ─────────────────────────────────────────────────────
        # 9. Fetch user permissions and check module / submodule
        # ─────────────────────────────────────────────────────
        permissions = get_user_permissions(tenant, user)

        # Module-level: permission at module level covers all submodules
        if has_permission(
            permissions,
            module=operation.endpoint.module,
            submodule=None,
            action=action_code,
        ):
            return self.get_response(request)

        # Submodule-level fallback
        if operation.endpoint.submodule and has_permission(
            permissions,
            module=operation.endpoint.module,
            submodule=operation.endpoint.submodule,
            action=action_code,
        ):
            return self.get_response(request)

        # ─────────────────────────────────────────────────────
        # 10. Final deny  (default-deny policy)
        # ─────────────────────────────────────────────────────
        # raise RBACPermissionDenied(
        #     violation_type=RBACPermissionDenied.PERMISSION_DENIED,
        #     detail=(
        #         f"User '{user}' does not have '{action_code}' permission on "
        #         f"module '{operation.endpoint.module}'"
        #         + (
        #             f" / submodule '{operation.endpoint.submodule}'"
        #             if operation.endpoint.submodule
        #             else ""
        #         )
        #         + f" required to access '{request.method} {path}'."
        #     ),
        # )
        return JsonResponse(
            {"data": {}, "success": False,
             "error": "User is not authorized",
             "message": "User is not authorized"},
            status=401
        )
