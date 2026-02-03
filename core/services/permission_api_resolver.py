from accounts.models import UserApiBlock
from core.models import (
    ApiEndpoint,
    ApiOperation,
    TenantApiOverride,
    ModuleSubModuleMapping,
    Permission,
)

DENY = False
ALLOW = True


# ─────────────────────────────
# API resolution
# ─────────────────────────────

def resolve_api_operation(request):
    endpoint = ApiEndpoint.objects.filter(
        path=request.path
    ).first()

    if not endpoint:
        return None

    return ApiOperation.objects.filter(
        endpoint=endpoint,
        http_method=request.method.upper(),
    ).first()


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
    Returns a set of permission tuples:
    (module_code, submodule_code | None, action_id)
    
    Join path: Permission → RolePermission → Role → UserRole → User
    Note: Module and SubModule use 'code' as primary key, not 'id'
    """

    qs = (
        Permission.objects.filter(
            tenant=tenant,
            roles__role__role_users__user=user,  # Fixed: role_users not user_roles
            roles__allowed=True,
        )
        .select_related(
            "tenant_module__module",
            "tenant_module__submodule",
            "action",
        )
        .values_list(
            "tenant_module__module__code",      # Use code, not id
            "tenant_module__submodule__code",   # Use code, not id
            "action_id",
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
        module.code,  # Module uses code as PK
        submodule.code if submodule else None,  # SubModule uses code as PK
        action.id,
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

    # Module-level permission
    if has_permission(
        permissions,
        module=operation.endpoint.module,
        submodule=None,
        action=operation.action,
    ):
        return ALLOW

    # Submodule-level permission
    if operation.endpoint.submodule and has_permission(
        permissions,
        module=operation.endpoint.module,
        submodule=operation.endpoint.submodule,
        action=operation.action,
    ):
        return ALLOW

    return DENY
