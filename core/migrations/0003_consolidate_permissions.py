# Generated manually to consolidate duplicate permissions before schema changes

from django.db import migrations


def consolidate_permissions(apps, schema_editor):
    """
    Consolidate duplicate permissions before removing the action field.
    For each unique (tenant, tenant_module) combination, keep one permission
    and delete the rest.
    """
    Permission = apps.get_model('core', 'Permission')
    RolePermission = apps.get_model('core', 'RolePermission')
    
    # Get all unique (tenant, tenant_module) combinations
    seen = set()
    to_delete = []
    to_keep = {}
    
    for perm in Permission.objects.all().order_by('id'):
        key = (perm.tenant_id, perm.tenant_module_id)
        
        if key not in seen:
            # First occurrence - keep this one
            seen.add(key)
            to_keep[key] = perm
        else:
            # Duplicate - mark for deletion
            to_delete.append(perm)
    
    # Migrate RolePermission references from duplicates to the kept permission
    for perm in to_delete:
        key = (perm.tenant_id, perm.tenant_module_id)
        kept_perm = to_keep[key]
        
        # Get all RolePermissions pointing to this duplicate
        role_perms = RolePermission.objects.filter(permission=perm)
        
        for rp in role_perms:
            # Check if a RolePermission already exists for this role and kept permission
            existing = RolePermission.objects.filter(
                role=rp.role,
                permission=kept_perm
            ).first()
            
            if existing:
                # Duplicate RolePermission - just delete this one
                rp.delete()
            else:
                # Update to point to kept permission
                rp.permission = kept_perm
                rp.save()
    
    # Delete duplicate permissions
    for perm in to_delete:
        perm.delete()
    
    print(f"Consolidated {len(to_delete)} duplicate permissions into {len(to_keep)} unique permissions")


def reverse_consolidation(apps, schema_editor):
    """
    Cannot reverse this migration - data has been consolidated.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_role_name'),
    ]

    operations = [
        migrations.RunPython(consolidate_permissions, reverse_consolidation),
    ]
