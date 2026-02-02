from core.models import Role, Permission
from accounts.models import UserRole, UserApiBlock
from core.services.rules import is_allowed
from collections import defaultdict


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
    return UserRole.objects.filter(
        user=user,
        roles__allowed=True,
    ).distinct()

def get_user_access(user):
    tenant_id = user.tenant.id
    roles = Role.objects.filter(
        role_users__user=user,
        role_users__user__tenant_id=tenant_id
    )

    permissions = Permission.objects.filter(
        roles__role__in=roles,
        tenant_id=tenant_id
    ).select_related(
        "tenant_module__module",
        "tenant_module__submodule",
    )

    blocked_apis = UserApiBlock.objects.filter(
        user=user,
        tenant_id=tenant_id
    )

    return roles, permissions, blocked_apis




def build_access_tree(permissions, blocked_apis):
    modules = {}
    submodule_index = {}  # quick lookup: (module_code, submodule_code)

    # -----------------------------
    # 1️⃣ Build module + submodule tree
    # -----------------------------
    for perm in permissions:
        print(perm, "<<<<<perm")
        m = perm.tenant_module.module
        sm = perm.tenant_module.submodule
        action = perm.action.code.lower()

        if m.code not in modules:
            modules[m.code] = {
                "code": m.code,
                "name": m.name,
                "permissions": {
                    "view": False,
                    "create": False,
                    "update": False,
                    "delete": False
                },
                "blocked_apis": [],
                "sub_modules": []
            }

        modules[m.code]["permissions"][action] = True

        if sm:
            key = (m.code, sm.code)

            if key not in submodule_index:
                sm_dict = {
                    "code": sm.code,
                    "name": sm.name,
                    "permissions": {
                        "view": False,
                        "create": False,
                        "update": False,
                        "delete": False
                    },
                    "blocked_apis": []
                }
                modules[m.code]["sub_modules"].append(sm_dict)
                submodule_index[key] = sm_dict

            submodule_index[key]["permissions"][action] = True

    # -----------------------------
    # 2️⃣ Attach blocked APIs
    # -----------------------------
    for block in blocked_apis:
        block_data = {
            "method": block.method,
            "path": block.path,
            "reason": block.reason
        }

        # 🔴 Sub-module level block
        if block.module and block.sub_module:
            key = (block.module.code, block.sub_module.code)
            if key in submodule_index:
                submodule_index[key]["blocked_apis"].append(block_data)

        # 🟠 Module level block
        elif block.module:
            mod = modules.get(block.module.code)
            if mod:
                mod["blocked_apis"].append(block_data)

        # ⚫ Global block (rare but useful)
        else:
            for mod in modules.values():
                mod["blocked_apis"].append(block_data)

    return list(modules.values())


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

    permissions = get_user_access(user)



    return sorted(allowed)
