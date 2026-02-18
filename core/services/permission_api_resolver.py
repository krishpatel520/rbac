from accounts.models import UserApiBlock
from core.models import ApiEndpoint, ApiOperation, TenantApiOverride, Permission
import re

from core.rbac.constants import HTTP_METHOD_ACTION_MAP

DENY = False
ALLOW = True




# ─────────────────────────────
# API resolution
# ─────────────────────────────
def resolve_api_operation(request):
    """
    Resolve API operation by matching request path + method.
    Supports parameterized URLs like /leads/{id}/
    """

    request_path = request.path.rstrip("/")
    method = request.method.upper()

    # 1️⃣ Exact match first
    endpoint = ApiEndpoint.objects.filter(path=request_path).first()
    if endpoint:
        return ApiOperation.objects.filter(endpoint=endpoint, http_method=method).first()

    # 2️⃣ Pattern match
    for endpoint in ApiEndpoint.objects.all():
        pattern = re.sub(r'\{(\w+)\}', r'[^/]+', endpoint.path)
        pattern = f'^{pattern.rstrip("/")}$'

        if re.match(pattern, request_path):
            return ApiOperation.objects.filter(endpoint=endpoint, http_method=method).first()

    return None


# ─────────────────────────────
# ABAC checks
# ─────────────────────────────

def tenant_api_disabled(tenant, operation):
    return TenantApiOverride.objects.filter(
        tenant=tenant,
        api_operation=operation,
        is_enabled=False,
    ).exists()


def user_api_blocked(tenant, user, operation):
    return UserApiBlock.objects.filter(
        tenant=tenant,
        user=user,
        api_operation=operation,
    ).exists()


# ─────────────────────────────
# RBAC permission resolution
# ─────────────────────────────


def get_user_permissions(tenant, user):
    """
    Returns permission tuples:
    (module_code, submodule_code, action_code)
    """

    qs = (
        Permission.objects.filter(
            tenant=tenant,
            roles__role__role_users__user=user,
            roles__allowed=True,
            is_active=True,
        )
        .select_related("module", "submodule")
        .values_list(
            "module__code",
            "submodule__code",
            "code",
        )
        .distinct()
    )

    return set(qs)


def has_permission(permissions, module, submodule, action):
    """
    Check if a permission tuple exists in the user's permissions set.
    
    Note: Module and SubModule use 'code' as primary key, not 'id'
    """
    key = (
        getattr(module, 'code', module),
        getattr(submodule, 'code', submodule) if submodule else None,
        action,
    )
    return key in permissions


# ─────────────────────────────
# Optional helper (non-middleware)
# ─────────────────────────────

def check_user_permission(request):
    user = request.user
    tenant = user.tenant

    operation = resolve_api_operation(request)
    if not operation or not operation.is_enabled:
        return DENY

    if tenant_api_disabled(tenant, operation):
        return DENY

    if user_api_blocked(tenant, user, operation):
        return DENY

    permissions = get_user_permissions(tenant, user)

    action_code = HTTP_METHOD_ACTION_MAP.get(operation.http_method, "view")
    endpoint = operation.endpoint

    # Module level
    if has_permission(permissions, endpoint.module, None, action_code):
        return ALLOW

    # Submodule level
    if endpoint.submodule and has_permission(
        permissions, endpoint.module, endpoint.submodule, action_code
    ):
        return ALLOW

    return DENY
