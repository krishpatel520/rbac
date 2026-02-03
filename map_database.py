"""
Script to map current database state for RBAC testing
"""
import os
import django
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rbac_project.settings')
django.setup()

from core.models import (
    Tenant, Role, Module, SubModule, Action, 
    TenantModule, Permission, RolePermission,
    ApiEndpoint, ApiOperation, TenantApiOverride
)
from accounts.models import User, UserRole, UserApiBlock

def print_section(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

# ============================================================
# 1. TENANTS
# ============================================================
print_section("TENANTS")
tenants = Tenant.objects.all()
for t in tenants:
    print(f"  [{t.id}] {t.name} (Active: {t.is_active})")

# ============================================================
# 2. USERS PER TENANT
# ============================================================
print_section("USERS PER TENANT")
for t in tenants:
    print(f"\n  Tenant: {t.name}")
    print("  " + "-" * 70)
    users = User.objects.filter(tenant=t)
    for u in users:
        roles_list = [ur.role.name for ur in u.user_roles.all()]
        roles_str = ", ".join(roles_list) if roles_list else "NO ROLES"
        print(f"    [{u.id}] {u.username} - Roles: {roles_str}")


# ============================================================
# 3. ROLES PER TENANT
# ============================================================
print_section("ROLES PER TENANT")
for t in tenants:
    print(f"\n  Tenant: {t.name}")
    print("  " + "-" * 70)
    roles = Role.objects.filter(tenant=t, is_deleted=False)
    for r in roles:
        perm_count = RolePermission.objects.filter(role=r, allowed=True).count()
        user_count = UserRole.objects.filter(role=r).count()
        print(f"    [{r.id}] {r.name}")
        print(f"         -> {perm_count} permissions, {user_count} users")

# ============================================================
# 4. MODULES & SUBMODULES
# ============================================================
print_section("GLOBAL MODULES & SUBMODULES")
modules = Module.objects.all()
for m in modules:
    print(f"  Module: [{m.code}] {m.name}")

print()
submodules = SubModule.objects.all()
for sm in submodules:
    print(f"  SubModule: [{sm.code}] {sm.name}")

# ============================================================
# 5. ACTIONS
# ============================================================
print_section("GLOBAL ACTIONS")
actions = Action.objects.all()
for a in actions:
    print(f"  [{a.id}] {a.code}")

# ============================================================
# 6. TENANT MODULES (What each tenant has access to)
# ============================================================
print_section("TENANT MODULES")
for t in tenants:
    print(f"\n  Tenant: {t.name}")
    print("  " + "-" * 70)
    tenant_mods = TenantModule.objects.filter(tenant=t)
    for tm in tenant_mods:
        submod_str = f" -> {tm.submodule.name}" if tm.submodule else ""
        enabled_str = "[+]" if tm.is_enabled else "[X]"
        print(f"    [{enabled_str}] {tm.module.name}{submod_str}")

# ============================================================
# 7. PERMISSIONS PER ROLE (Sample from first tenant)
# ============================================================
print_section("SAMPLE PERMISSIONS (First Tenant)")
if tenants.exists():
    t = tenants.first()
    print(f"  Tenant: {t.name}\n")
    roles = Role.objects.filter(tenant=t, is_deleted=False)
    
    for r in roles:
        print(f"  Role: {r.name}")
        print("  " + "-" * 70)
        role_perms = RolePermission.objects.filter(role=r, allowed=True).select_related(
            'permission__tenant_module__module',
            'permission__tenant_module__submodule',
            'permission__action'
        )
        
        if role_perms.exists():
            for rp in role_perms[:10]:  # Limit to first 10
                perm = rp.permission
                module = perm.tenant_module.module.name
                submodule = perm.tenant_module.submodule.name if perm.tenant_module.submodule else "N/A"
                action = perm.action.code
                print(f"    [+] {module}/{submodule} : {action}")
            
            if role_perms.count() > 10:
                print(f"    ... and {role_perms.count() - 10} more")
        else:
            print("    (No permissions)")
        print()

# ============================================================
# 8. API ENDPOINTS
# ============================================================
print_section("API ENDPOINTS")
endpoints = ApiEndpoint.objects.all()
for ep in endpoints:
    submod_str = f" -> {ep.submodule.name}" if ep.submodule else ""
    print(f"  {ep.path}")
    print(f"    Module: {ep.module.name}{submod_str}")
    
    # Show operations for this endpoint
    ops = ApiOperation.objects.filter(endpoint=ep)
    for op in ops:
        enabled_str = "[+]" if op.is_enabled else "[X]"
        print(f"      [{enabled_str}] {op.http_method} -> {op.action.code}")
    print()

# ============================================================
# 9. TENANT API OVERRIDES
# ============================================================
print_section("TENANT API OVERRIDES")
overrides = TenantApiOverride.objects.all()
if overrides.exists():
    for override in overrides:
        enabled_str = "[+]" if override.is_enabled else "[X] DISABLED"
        print(f"  {override.tenant.name}: {override.api_operation.endpoint.path}")
        print(f"    {override.api_operation.http_method} [{enabled_str}]")
else:
    print("  (No overrides)")

# ============================================================
# 10. USER API BLOCKS
# ============================================================
print_section("USER API BLOCKS")
blocks = UserApiBlock.objects.all()
if blocks.exists():
    for block in blocks:
        print(f"  {block.user.username} @ {block.tenant.name}")
        print(f"    BLOCKED: {block.api_operation.endpoint.path} ({block.api_operation.http_method})")
        if block.reason:
            print(f"    Reason: {block.reason}")
else:
    print("  (No blocks)")

print("\n" + "=" * 80)
print(" MAPPING COMPLETE")
print("=" * 80 + "\n")
