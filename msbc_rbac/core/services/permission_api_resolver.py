from msbc_rbac.accounts.models import UserApiBlock
from msbc_rbac.core.models import ApiEndpoint, ApiOperation, TenantApiOverride, Permission, TenantModule, Permission, \
    TenantApiOverride, Role
import re

from msbc_rbac.core.rbac.constants import HTTP_METHOD_ACTION_MAP

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
    if not tenant and not user:
        raise Exception("Tenant or user must be specified")

    if not tenant and not user.get_attr("tenant", None):
        raise Exception("No tenant found for user")

    tenant = tenant if tenant else user.tenant

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

def perm_flags(perms):
    """
    Converts a list of permission strings into a dictionary of boolean flags.

    Args:
        perms: List of permission strings (e.g., ['invoice.read', 'invoice.create'])

    Returns:
        dict: Dictionary with keys 'read', 'create', 'update', 'delete', 'approve'
              and boolean values.
    """
    return {
        "read": any("read" in p or "view" in p for p in perms),
        "create": any("create" in p for p in perms),
        "update": any("update" in p for p in perms),
        "delete": any("delete" in p for p in perms),
        "approve": any("approve" in p for p in perms),
    }


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


def get_user_role_permission(tenant, user):
    # 1. Enabled Modules for Tenant
    enabled_matches = (
        TenantModule.objects
        .filter(tenant=tenant, is_enabled=True)
        .select_related("module", "submodule")
    )

    # 2. User Permissions (Replica of permission_api_resolver logic but with objects)
    permissions = Permission.objects.filter(
        tenant=tenant,
        roles__role__role_users__user=user,
        roles__allowed=True,
        is_active=True
    ).select_related("module", "submodule").distinct()

    # 3. Blocked APIs

    blocked_apis = UserApiBlock.objects.filter(
        tenant=tenant,
        user=user,
    ).select_related("api_operation__endpoint__module", "api_operation__endpoint__submodule")

    tenant_blocks = TenantApiOverride.objects.filter(
        tenant=tenant,
        is_enabled=False
    ).select_related("api_operation__endpoint__module", "api_operation__endpoint__submodule")

    # 4. Build Access Tree
    modules = {}
    submodule_index = {}

    # Initialize modules/submodules from enabled modules
    for tm in enabled_matches:
        m = tm.module
        sm = tm.submodule

        if m.pk not in modules:
            modules[m.pk] = {
                "code": m.pk,
                "name": m.name,
                "permissions": set(),
                "blocked_apis": [],
                "sub_modules": []
            }
        if sm:
            key = (m.pk, sm.pk)
            if key not in submodule_index:
                sm_dict = {
                    "code": sm.pk,
                    "name": sm.name,
                    "permissions": set(),
                    "blocked_apis": []
                }
                modules[m.pk]["sub_modules"].append(sm_dict)
                submodule_index[key] = sm_dict

    for perm in permissions:
        m = perm.module
        sm = perm.submodule
        code = perm.code.lower()  # invoice.read, invoice.approve

        if m.pk in modules:
            modules[m.pk]["permissions"].add(code)

            if sm and (m.pk, sm.pk) in submodule_index:
                submodule_index[(m.pk, sm.pk)]["permissions"].add(code)

    # 5. Attach Blocks
    for block in blocked_apis:
        op = block.api_operation
        ep = op.endpoint

        data = {
            "method": op.http_method,
            "path": ep.path,
            "reason": getattr(block, "reason", None)
        }

        if ep.submodule:
            key = (ep.module.pk, ep.submodule.pk)
            if key in submodule_index:
                submodule_index[key]["blocked_apis"].append(data)
        else:
            if ep.module.pk in modules:
                modules[ep.module.pk]["blocked_apis"].append(data)

    for block in tenant_blocks:
        op = block.api_operation
        ep = op.endpoint

        data = {
            "method": op.http_method,
            "path": ep.path,
            "reason": getattr(block, "reason", None)
        }

        if ep.submodule:
            key = (ep.module.pk, ep.submodule.pk)
            if key in submodule_index:
                submodule_index[key]["blocked_apis"].append(data)
        else:
            if ep.module.pk in modules:
                modules[ep.module.pk]["blocked_apis"].append(data)

    for m in modules.values():

        module_permissions = perm_flags(m["permissions"])
        m["permissions"] = module_permissions

        for sm in m["sub_modules"]:

            submodule_permissions = perm_flags(sm["permissions"])

            for perm, value in module_permissions.items():
                if value:
                    submodule_permissions[perm] = True

            sm["permissions"] = submodule_permissions

    return {
        "modules": list(modules.values()),
        "global_blocked_apis": blocked_apis,
        "roles": Role.objects.filter(tenant=tenant, role_users__user=user)
        .values("name", "id"),
    }

