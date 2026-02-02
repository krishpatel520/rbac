from accounts.models import UserApiBlock
from core.models import ApiEndpoint, ApiOperation, TenantApiOverride, ModuleSubModuleMapping, Permission
DENY = False
ALLOW = True

def resolve_api_operation(request):
    # from .models import ApiEndpoint, ApiOperation

    endpoint = ApiEndpoint.objects.filter(
        path=request.path
    ).first()

    if not endpoint:
        return None

    operation = ApiOperation.objects.filter(
        endpoint=endpoint,
        http_method=request.method.upper()
    ).first()

    return operation

def tenant_api_disabled(tenant, operation):
    # from .models import TenantApiOverride

    return TenantApiOverride.objects.filter(
        tenant=tenant,
        api_operation=operation,
        is_enabled=False
    ).exists()

def user_api_blocked(tenant, user, operation):
    # from .models import UserApiBlock

    return UserApiBlock.objects.filter(
        tenant=tenant,
        user=user,
        api_operation=operation
    ).exists()

def get_resource(tenant, module, submodule):
    # from .models import Resource

    return ModuleSubModuleMapping.objects.get(
        tenant=tenant,
        module=module,
        submodule=submodule
    )

def get_user_permissions(tenant, user):
    # from .models import Permission

    return set(
        Permission.objects.filter(
            tenant=tenant,
            rolepermission__role__userrole__user=user
        ).values_list(
            'resource__module_id',
            'resource__submodule_id',
            'action_id'
        )
    )

def has_permission(permissions, module, submodule, action):
    key = (
        module.id,
        submodule.id if submodule else None,
        action.id
    )
    return key in permissions


def check_user_permission(request):
    user = request.user
    tenant = user.tenant

    operation = resolve_api_operation(request)
    if not operation or not operation.is_enabled:
        return DENY

    if tenant_api_disabled(tenant, operation):
        return DENY

    if user_api_blocked(tenant, user, operation):
        return DENY  # 🔥 explicit deny

    resource = get_resource(
        tenant=tenant,
        module=operation.endpoint.module,
        submodule=operation.endpoint.submodule
    )

    permissions = get_user_permissions(tenant, user)

    # Module-level permission
    if has_permission(
            permissions,
            module=resource.module,
            submodule=None,
            action=operation.action
    ):
        return ALLOW

    # Submodule fallback
    if resource.submodule and has_permission(
            permissions,
            module=resource.module,
            submodule=resource.submodule,
            action=operation.action
    ):
        return ALLOW

    return DENY


