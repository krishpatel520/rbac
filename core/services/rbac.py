from core.models import Role, Permission


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
    if not user or not user.is_authenticated:
        return False

    return Permission.objects.filter(
        code=permission_code,
        roles__role__role_users__user=user,
        roles__allowed=True,
    ).exists()
