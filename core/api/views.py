from rest_framework import serializers
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response

from core.api.base import RBACViewSet
from core.models import Role, Tenant, Module
from accounts.models import User

# 1. Serializers
class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'is_active']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'is_deleted']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active']

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['code', 'name']

# 2. ViewSets
class TenantViewSet(RBACViewSet):
    """
    Demo ViewSet for Tenants (Global read usually, or strict RBAC)
    NOTE: Tenant is not tenant-scoped in the same way, so we override get_queryset.
    """
    serializer_class = TenantSerializer
    queryset = Tenant.objects.all()

    def get_queryset(self):
        # A user can usually only see their own tenant? 
        # Or maybe for this demo we let them see all if they have permission?
        # Let's restrict to own tenant for safety + Admin usually sees all.
        # But 'tenant' field doesn't exist on Tenant model obviously.
        # Let's just return request.user.tenant to be safe and demonstrate isolation.
        if self.request.user.is_superuser:
            return Tenant.objects.all()
        return Tenant.objects.filter(id=self.request.user.tenant.id)

class RoleViewSet(RBACViewSet):
    """
    RBAC-protected Role management.
    """
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    # Uses standard tenant_field='tenant' from base class

class UserViewSet(RBACViewSet):
    """
    RBAC-protected User management.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    # Uses standard tenant_field='tenant' from base class

class ModuleViewSet(RBACViewSet):
    """
    Read-only view of modules.
    """
    serializer_class = ModuleSerializer
    queryset = Module.objects.all()
    
    def get_queryset(self):
        # Modules are global, not tenant scoped.
        return Module.objects.all()

# 3. Router
router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserViewSet, basename='user')
# router.register(r'tenants', TenantViewSet, basename='tenant') # Optional
# router.register(r'modules', ModuleViewSet, basename='module') # Optional
