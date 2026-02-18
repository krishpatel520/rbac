from core.models import (
    Module,
    SubModule,
    TenantModule,
    Permission,
)
from core.serializers import serialize_tenant_modules, serialize_modules


def build_sidebar_context(user):
    tenant = getattr(user, "tenant", None)

    # ─────────────────────────────
    # SUPER ADMIN (GLOBAL SIDEBAR)
    # ─────────────────────────────
    if user.is_superuser:
        modules = (
            Module.objects.all()
            .prefetch_related("submodules")
            .order_by("order")
        )

        return serialize_modules(modules)

    # ─────────────────────────────
    # TENANT USERS (ADMIN + NORMAL)
    # ─────────────────────────────

    # Enabled modules for tenant
    tenant_modules = (
        TenantModule.objects.filter(tenant=tenant, is_enabled=True)
        .select_related("module", "submodule")
    )

    # User permissions
    permissions = Permission.objects.filter(
        tenant=tenant,
        roles__role__role_users__user=user,
        roles__allowed=True,
    ).select_related("module", "submodule")

    return serialize_tenant_modules(tenant_modules, permissions)
