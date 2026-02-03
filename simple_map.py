"""
Simple script to map database state - writes to file
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rbac_project.settings')
django.setup()

from core.models import *
from accounts.models import *

# Write to file instead of console
with open('db_state.txt', 'w', encoding='utf-8') as f:
    def p(text=""):
        f.write(text + "\n")
        print(text)
    
    p("=" * 80)
    p("DATABASE STATE MAPPING")
    p("=" * 80)
    
    # TENANTS
    p("\n1. TENANTS")
    p("-" * 80)
    tenants = Tenant.objects.all()
    for t in tenants:
        p(f"  [{t.id}] {t.name} (Active: {t.is_active})")
    
    # USERS
    p("\n2. USERS PER TENANT")
    p("-" * 80)
    for t in tenants:
        p(f"\n  Tenant: {t.name}")
        users = User.objects.filter(tenant=t)
        for u in users:
            roles = [ur.role.name for ur in u.user_roles.all()]
            roles_str = ", ".join(roles) if roles else "NO ROLES"
            p(f"    [{u.id}] {u.username} - {roles_str}")
    
    # ROLES
    p("\n3. ROLES PER TENANT")
    p("-" * 80)
    for t in tenants:
        p(f"\n  Tenant: {t.name}")
        roles = Role.objects.filter(tenant=t, is_deleted=False)
        for r in roles:
            perm_count = RolePermission.objects.filter(role=r, allowed=True).count()
            user_count = UserRole.objects.filter(role=r).count()
            p(f"    [{r.id}] {r.name} - {perm_count} perms, {user_count} users")
    
    # MODULES
    p("\n4. MODULES & SUBMODULES")
    p("-" * 80)
    modules = Module.objects.all()
    for m in modules:
        p(f"  Module: [{m.code}] {m.name}")
    p("")
    submodules = SubModule.objects.all()
    for sm in submodules:
        p(f"  SubModule: [{sm.code}] {sm.name}")
    
    # ACTIONS
    p("\n5. ACTIONS")
    p("-" * 80)
    actions = Action.objects.all()
    for a in actions:
        p(f"  [{a.id}] {a.code}")
    
    # TENANT MODULES
    p("\n6. TENANT MODULES (What each tenant has enabled)")
    p("-" * 80)
    for t in tenants:
        p(f"\n  Tenant: {t.name}")
        tenant_mods = TenantModule.objects.filter(tenant=t)
        for tm in tenant_mods:
            submod = f" -> {tm.submodule.name}" if tm.submodule else ""
            status = "[ENABLED]" if tm.is_enabled else "[DISABLED]"
            p(f"    {status} {tm.module.name}{submod}")
    
    # SAMPLE PERMISSIONS
    p("\n7. PERMISSIONS BREAKDOWN (First Tenant)")
    p("-" * 80)
    if tenants.exists():
        t = tenants.first()
        p(f"  Tenant: {t.name}\n")
        roles = Role.objects.filter(tenant=t, is_deleted=False)
        for r in roles:
            p(f"  Role: {r.name}")
            role_perms = RolePermission.objects.filter(role=r, allowed=True).select_related(
                'permission__tenant_module__module',
                'permission__tenant_module__submodule',
                'permission__action'
            )[:15]
            for rp in role_perms:
                perm = rp.permission
                mod = perm.tenant_module.module.name
                sub = perm.tenant_module.submodule.name if perm.tenant_module.submodule else "N/A"
                act = perm.action.code
                p(f"    - {mod}/{sub} : {act}")
            total = RolePermission.objects.filter(role=r, allowed=True).count()
            if total > 15:
                p(f"    ... and {total - 15} more")
            p("")
    
    # API ENDPOINTS
    p("\n8. API ENDPOINTS")
    p("-" * 80)
    endpoints = ApiEndpoint.objects.all()
    for ep in endpoints:
        submod = f" -> {ep.submodule.name}" if ep.submodule else ""
        p(f"  {ep.path}")
        p(f"    Module: {ep.module.name}{submod}")
        ops = ApiOperation.objects.filter(endpoint=ep)
        for op in ops:
            status = "[ENABLED]" if op.is_enabled else "[DISABLED]"
            p(f"      {status} {op.http_method} -> {op.action.code}")
    
    # OVERRIDES
    p("\n9. TENANT API OVERRIDES")
    p("-" * 80)
    overrides = TenantApiOverride.objects.all()
    if overrides.exists():
        for ov in overrides:
            status = "[ENABLED]" if ov.is_enabled else "[DISABLED]"
            p(f"  {ov.tenant.name}: {ov.api_operation.endpoint.path} {ov.api_operation.http_method} {status}")
    else:
        p("  (No overrides)")
    
    # BLOCKS
    p("\n10. USER API BLOCKS")
    p("-" * 80)
    blocks = UserApiBlock.objects.all()
    if blocks.exists():
        for b in blocks:
            p(f"  {b.user.username} @ {b.tenant.name}")
            p(f"    BLOCKED: {b.api_operation.endpoint.path} ({b.api_operation.http_method})")
            if b.reason:
                p(f"    Reason: {b.reason}")
    else:
        p("  (No blocks)")
    
    p("\n" + "=" * 80)
    p("COMPLETE - See db_state.txt for full output")
    p("=" * 80)

print("\nDone! Check db_state.txt for full output")
