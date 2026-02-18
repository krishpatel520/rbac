from django.contrib import admin

from core.models import (
    Tenant,
    Module,
    TenantModule,
    Role,
    Permission,
    RolePermission, ModuleSubModuleMapping, ApiEndpoint, ApiOperation, TenantApiOverride,
)
from accounts.models import UserRole


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ( "code", "name")
    search_fields = ("code", "name")


@admin.register(TenantModule)
class TenantModuleAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "module", "is_enabled")
    list_filter = ("tenant", "module", "is_enabled")
    search_fields = ("tenant__name", "module__code")
    autocomplete_fields = ("tenant", "module")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "tenant", "is_deleted")
    list_filter = ("tenant", "is_deleted")
    search_fields = ("name", "tenant__name")

    def delete_model(self, request, obj):
        # Preserve soft-delete semantics
        obj.delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("tenant", "module", "submodule", "code", "is_active")
    search_fields = ("code", "description")


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "get_tenant", "permission", "allowed")
    list_filter = ("role__tenant", "allowed")
    search_fields = ("role__name", "role__tenant__name")
    autocomplete_fields = ("role", "permission")

    def get_tenant(self, obj):
        """Display tenant from the related role."""
        return obj.role.tenant
    get_tenant.short_description = "Tenant"
    get_tenant.admin_order_field = "role__tenant"


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "role__name")
    autocomplete_fields = ("user", "role")


@admin.register(ModuleSubModuleMapping)
class ModuleSubModuleMappingAdmin(admin.ModelAdmin):
    list_display = ("module", "submodule")


#@admin.register(Action)
#class ActionModelAdmin(admin.ModelAdmin):
#    list_display = ("id", "code")


@admin.register(ApiEndpoint)
class ApiEndpointAdmin(admin.ModelAdmin):
    list_display = ("id", "module","submodule","path")


@admin.register(ApiOperation)
class ApiOperationAdmin(admin.ModelAdmin):
    list_display = ("id", "endpoint", "http_method", "permission_code", "is_enabled")


@admin.register(TenantApiOverride)
class TenantApiOverrideAdmin(admin.ModelAdmin):
    list_display = ("id", "api_operation","is_enabled")


