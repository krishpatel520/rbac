from django.db import models
from django.conf import settings
from django.utils import timezone


# ----------------------------
# Tenant
# ----------------------------
class Tenant(models.Model):
    """
    Represents one organization / company.
    """
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ----------------------------
# Role (GLOBAL)
# ----------------------------
class Role(models.Model):
    """
    Global role definition (e.g. Admin, SalesExecutive).
    """
    name = models.CharField(max_length=100, unique=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        """
        Soft delete for safety.
        """
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_deleted", "deleted_at"])

    def __str__(self):
        return self.name


# ----------------------------
# Permission (GLOBAL)
# ----------------------------
class Permission(models.Model):
    """
    Global permission definition.
    Example: enquiry.create, quotation.approve
    """
    code = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.code


# ----------------------------
# Role ↔ Permission (GLOBAL)
# ----------------------------
class RolePermission(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="roles",
    )
    allowed = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="unique_role_permission",
            )
        ]

    def __str__(self):
        return f"{self.role} → {self.permission}"


class Module(models.Model):
    """"
    Represents a CRM sub-module.
    Examples: Enquiry, Quotation, FollowUp, Organization
    """
    code = models.CharField(max_length=50, unique = True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

class TenantModule(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="modules",
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="tenants",
    )
    is_enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "module"],
                name="unique_tenant_module",
            )
        ]
    def __str__(self):
        return f"{self.tenant} → {self.module}"