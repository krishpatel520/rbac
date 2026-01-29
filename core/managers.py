from django.db import models
from core.tenant_context import get_current_tenant


class TenantAwareQuerySet(models.QuerySet):
    def for_tenant(self):
        tenant = get_current_tenant()
        if tenant is None:
            return self.none()
        return self.filter(tenant=tenant)


class TenantAwareManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()

        if tenant is None:
            return qs.none()

        return qs.filter(tenant=tenant)
