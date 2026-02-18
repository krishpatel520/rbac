from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.models import TenantModule, Permission, TenantApiOverride, Role
from accounts.models import UserApiBlock
from core.serializers import serialize_tenant_modules
from core.services.sidebar_context import build_sidebar_context


# from core.utils import get_user_allowed_actions, get_user_access, build_access_tree # Deleted


@login_required
def dashboard(request):
    """
    Canonical post-login dashboard.

    Shows:
    - Active tenant
    - Enabled modules for tenant
    - Allowed actions per module (RBAC + ABAC)
    """

    user = request.user
    tenant = user.tenant

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
        m["permissions"] = perm_flags(m["permissions"])
        for sm in m["sub_modules"]:
            sm["permissions"] = perm_flags(sm["permissions"])

    return render(
        request,
        "core/dashboard.html",
        {
            "tenant": tenant,
            "modules": list(modules.values()),
            "global_blocked_apis": blocked_apis,
            "roles": Role.objects.filter(tenant=tenant, role_users__user=user)
            .values("name", "id"),
        },
    )



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
        "read": any(".read" in p for p in perms),
        "create": any(".create" in p for p in perms),
        "update": any(".update" in p for p in perms),
        "delete": any(".delete" in p for p in perms),
        "approve": any(".approve" in p for p in perms),
    }


def sidebar_context(request):
    """
    Context processor to inject sidebar modules into templates.
    """
    if not request.user.is_authenticated:
        return {}

    return {
        "sidebar_modules": build_sidebar_context(request.user)
    }