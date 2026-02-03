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

    class Meta:
        db_table = "tenant"

    def __str__(self):
        return self.name


# ----------------------------
# Role (GLOBAL)
# ----------------------------
class Role(models.Model):
    """
    Global role definition (e.g. Admin, SalesExecutive).
    """
    name = models.CharField(max_length=100)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "admin_role"
        unique_together = ('name', 'tenant')

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

    def delete(self, *args, **kwargs):
        """
        Soft delete for safety.
        """
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_deleted", "deleted_at"])


# ----------------------------
# Permission (GLOBAL)
# ----------------------------
# class Permission(models.Model):
#     """
#     Global permission definition.
#     Example: enquiry.create, quotation.approve
#     """
#     code = models.CharField(max_length=150, unique=True)
#     description = models.TextField(blank=True)
#
#     def __str__(self):
#         return self.code
#


class Module(models.Model):
    """"
    Represents a CRM module.
    Examples: CRM , BULk
    """
    code = models.CharField(primary_key=True,max_length=50, unique = True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "admin_module"


class SubModule(models.Model):
    """"
    Represents a CRM sub-module.
    Examples: Enquiry, Quotation, FollowUp, Organization
    """
    code = models.CharField(primary_key=True,max_length=50, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "admin_sub_module"

    def __str__(self):
        return self.name

class Action(models.Model):
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = "admin_action"


class ModuleSubModuleMapping(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    submodule = models.ForeignKey(SubModule, on_delete=models.CASCADE)

    class Meta:
        db_table = "admin_mod_submodule_mapping"
        unique_together = ('module', 'submodule')


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
    submodule = models.ForeignKey(
        SubModule, null=True, blank=True, on_delete=models.CASCADE
    )
    is_enabled = models.BooleanField(default=True)
    expiration_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "admin_tenant_module"

        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "module","submodule"],
                name="unique_tenant_module_submodule",
            )
        ]
    def __str__(self):
        return f"{self.tenant} → {self.module}"

class Permission(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    tenant_module = models.ForeignKey(TenantModule, on_delete=models.CASCADE)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)

    class Meta:
        db_table = "admin_permission"
        unique_together = ('tenant', 'tenant_module', 'action')

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
        db_table = "admin_role_permission_mapping"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="unique_role_permission",
            )
        ]

    def __str__(self):
        return f"{self.role} → {self.permission}"

class ApiEndpoint(models.Model):
    path = models.CharField(max_length=200)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    submodule = models.ForeignKey(
        SubModule, null=True, blank=True, on_delete=models.CASCADE
    )

    class Meta:
        db_table = "admin_api_details"


class ApiOperation(models.Model):
    endpoint = models.ForeignKey(ApiEndpoint, on_delete=models.CASCADE)
    http_method = models.CharField(max_length=10)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "admin_api_operation"
        unique_together = ('endpoint', 'http_method')

class TenantApiOverride(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    api_operation = models.ForeignKey(ApiOperation, on_delete=models.CASCADE)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "admin_tenant_api_operation"

        unique_together = ('tenant', 'api_operation')


