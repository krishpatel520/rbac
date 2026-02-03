"""
Script to fix API endpoint module mappings
Currently all endpoints are mapped to "System" but should be mapped to CRM/Ops
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rbac_project.settings')
django.setup()

from core.models import ApiEndpoint, Module, SubModule

# Get modules
crm_module = Module.objects.get(code='CRM')
ops_module = Module.objects.get(code='OPS')
system_module = Module.objects.get(code='SYSTEM')

# Get submodules
leads_sub = SubModule.objects.get(code='LEADS')
deals_sub = SubModule.objects.get(code='DEALS')
tasks_sub = SubModule.objects.get(code='TASKS')
reports_sub = SubModule.objects.get(code='REPORTS')

print("=" * 80)
print("FIXING API ENDPOINT MODULE MAPPINGS")
print("=" * 80)

# Mapping rules based on endpoint paths
mappings = [
    # Enquiries -> CRM/Leads
    {
        'path_contains': 'enquiries',
        'module': crm_module,
        'submodule': leads_sub,
        'description': 'Enquiries -> CRM/Leads'
    },
    # Quotations -> CRM/Deals
    {
        'path_contains': 'quotations',
        'module': crm_module,
        'submodule': deals_sub,
        'description': 'Quotations -> CRM/Deals'
    },
    # Followups -> Ops/Tasks
    {
        'path_contains': 'followups',
        'module': ops_module,
        'submodule': tasks_sub,
        'description': 'Followups -> Ops/Tasks'
    },
    # Organizations -> Ops/Reports
    {
        'path_contains': 'organizations',
        'module': ops_module,
        'submodule': reports_sub,
        'description': 'Organizations -> Ops/Reports'
    },
]

updated_count = 0

for mapping in mappings:
    endpoints = ApiEndpoint.objects.filter(path__icontains=mapping['path_contains'])
    
    print(f"\n{mapping['description']}")
    print("-" * 80)
    
    for ep in endpoints:
        old_module = ep.module.name if ep.module else "None"
        old_submodule = ep.submodule.name if ep.submodule else "None"
        
        ep.module = mapping['module']
        ep.submodule = mapping['submodule']
        ep.save()
        
        print(f"  {ep.path}")
        print(f"    WAS: {old_module}/{old_submodule}")
        print(f"    NOW: {mapping['module'].name}/{mapping['submodule'].name}")
        
        updated_count += 1

# Handle root paths and docs - keep as System
system_paths = ['/', '/api/', '/api/docs/']
print(f"\n\nKeeping System Module for Infrastructure Paths")
print("-" * 80)
for path in system_paths:
    endpoints = ApiEndpoint.objects.filter(path__iexact=path)
    for ep in endpoints:
        if ep.module != system_module:
            ep.module = system_module
            ep.submodule = None
            ep.save()
            print(f"  {ep.path} -> System (no submodule)")

print("\n" + "=" * 80)
print(f"COMPLETE - Updated {updated_count} endpoints")
print("=" * 80)

# Verify the changes
print("\n\nVERIFYING CHANGES:")
print("=" * 80)

print("\nCRM/Leads endpoints:")
for ep in ApiEndpoint.objects.filter(module=crm_module, submodule=leads_sub)[:5]:
    print(f"  {ep.path}")

print("\nCRM/Deals endpoints:")
for ep in ApiEndpoint.objects.filter(module=crm_module, submodule=deals_sub)[:5]:
    print(f"  {ep.path}")

print("\nOps/Tasks endpoints:")
for ep in ApiEndpoint.objects.filter(module=ops_module, submodule=tasks_sub)[:5]:
    print(f"  {ep.path}")

print("\nOps/Reports endpoints:")
for ep in ApiEndpoint.objects.filter(module=ops_module, submodule=reports_sub)[:5]:
    print(f"  {ep.path}")

print("\nSystem endpoints:")
for ep in ApiEndpoint.objects.filter(module=system_module):
    print(f"  {ep.path}")

print("\n✓ API endpoint module mappings fixed successfully!")
