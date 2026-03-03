from django.db import models
from core.tenant_context import get_current_tenant


class TenantAwareQuerySet(models.QuerySet):
    """
    Custom QuerySet that filters results by the current tenant.
    """
    def for_tenant(self):
        """
        Filters the queryset to include only objects belonging to the current tenant.
        """
        tenant = get_current_tenant()
        if tenant is None:
            return self.none()
        return self.filter(tenant=tenant)


class TenantAwareManager(models.Manager):
    """
    Custom Manager that uses TenantAwareQuerySet to automatically filter by tenant.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()

        if tenant is None:
            return qs.none()

        return qs.filter(tenant=tenant)
