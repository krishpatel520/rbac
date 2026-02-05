from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.models import TenantModule, Permission
from accounts.models import UserApiBlock
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
    ).select_related(
        "tenant_module__module",
        "tenant_module__submodule",
        "action",
    ).distinct()

    # 3. Blocked APIs
    blocked_apis = UserApiBlock.objects.filter(
        tenant=tenant,
        user=user,
    ).select_related("api_operation__endpoint")

    # 4. Build Access Tree
    modules = {}
    submodule_index = {}

    for perm in permissions:
        m = perm.tenant_module.module
        sm = perm.tenant_module.submodule
        action = perm.action.code.lower()

        # Init Module
        if m.code not in modules:
            modules[m.code] = {
                "code": m.code,
                "name": m.name,
                "permissions": {
                    "view": False, "create": False, "update": False, "delete": False
                },
                "blocked_apis": [],
                "sub_modules": []
            }

        modules[m.code]["permissions"][action] = True

        # Init Submodule
        if sm:
            key = (m.code, sm.code)
            if key not in submodule_index:
                sm_dict = {
                    "code": sm.code,
                    "name": sm.name,
                    "permissions": {
                        "view": False, "create": False, "update": False, "delete": False
                    },
                    "blocked_apis": []
                }
                modules[m.code]["sub_modules"].append(sm_dict)
                submodule_index[key] = sm_dict

            submodule_index[key]["permissions"][action] = True

    # 5. Attach Blocks
    for block in blocked_apis:
        block_data = {
            "method": block.api_operation.http_method,
            "path": block.api_operation.endpoint.path,
            "reason": block.reason
        }
        # Simplified: Attach to all modules for now as Global Block or find specific module
        # In this refactor, we just list them separately or simplistic attachment
        pass 

    return render(
        request,
        "core/dashboard.html",
        {
            "tenant": tenant,
            "modules": list(modules.values()),
            "global_blocked_apis": blocked_apis, 
            "roles": user.user_roles.filter(role__tenant=tenant).values("role__name", "role__id"),
        },
    )

