from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.models import TenantModule, Module
from core.utils import get_user_allowed_actions, get_user_access, build_access_tree


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

    enabled_modules = (
        TenantModule.objects
        .filter(tenant=tenant, is_enabled=True)
        .select_related("module","submodule")
    )
    print("enabled_modules >>>>",enabled_modules)

    module_actions = {}

    # Permission-centric dashboard (Option A)
    # actions = get_user_allowed_actions(user)

    roles, permissions, blocked_apis = get_user_access(
        request.user,
    )

    response = {
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
        },
        "roles": list(roles.values("id",  "name")),
        "modules": build_access_tree(permissions, blocked_apis),
        "blocked_apis": list(blocked_apis.values(
            "api_operation__http_method", "api_operation__endpoint", "reason"
        ))
    }

    print("response>>>",response)

    return render(
        request,
        "core/dashboard.html",
        {
            "tenant": tenant,
            "modules": response["modules"],  # ✅ list of modules
            "global_blocked_apis": response.get("blocked_apis", []),
            "roles": response.get("roles", []),
        },
    )

