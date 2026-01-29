from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.models import TenantModule, Module
from core.utils import get_user_allowed_actions


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
        .select_related("module")
    )

    module_actions = {}

    # Permission-centric dashboard (Option A)
    actions = get_user_allowed_actions(user)

    for tenant_module in enabled_modules:
        module = tenant_module.module

        module_actions[module.code] = [
        action
        for action in actions
        if action.startswith(f"{module.code}.")
        ]


    return render(
        request,
        "core/dashboard.html",
        {
            "tenant": tenant,
            "module_actions": module_actions,
        },
    )
