from core.models import Role, Permission
from accounts.models import UserRole
from core.services.rules import is_allowed


def get_roles_for_user(user):
    return Role.objects.filter(
        role_users__user=user,
        is_deleted=False,
    ).distinct()


def get_permissions_for_user(user):
    """
    RBAC resolution:

    User
      → UserRole
        → Role
          → RolePermission (allowed=True)
            → Permission
    """
    return Permission.objects.filter(
        roles__role__role_users__user=user,
        roles__allowed=True,
    ).distinct()


def has_permission(user, permission_code: str) -> bool:
    if not user.is_authenticated:
        return False

    return Permission.objects.filter(
        code=permission_code,
        roles__role__role_users__user=user,
        roles__allowed=True,
    ).exists()


def get_user_allowed_actions(user):
    """
    Returns a list of permission codes the user is currently allowed to perform,
    after RBAC + ABAC evaluation.
    """

    if not user.is_authenticated:
        return []

    allowed = []

    permissions = get_permissions_for_user(user)

    for perm in permissions:
        if is_allowed(user, perm.code, obj=None):
            allowed.append(perm.code)

    return sorted(allowed)
