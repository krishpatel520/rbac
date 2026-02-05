"""
Django management command to clean up and fix API endpoint registrations.

This command:
1. Cleans regex patterns from paths
2. Fixes module/submodule mappings
3. Adds missing operations (UPDATE, DELETE)
4. Removes unused actions
5. Consolidates duplicate format suffix endpoints

Usage:
    python manage.py cleanup_api_endpoints --dry-run  # Preview changes
    python manage.py cleanup_api_endpoints             # Execute cleanup
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    ApiEndpoint,
    ApiOperation,
    Action,
    Module,
    SubModule,
)
import re


class Command(BaseCommand):
    help = "Clean up and fix API endpoint registrations"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )
        parser.add_argument(
            '--skip-paths',
            action='store_true',
            help='Skip path cleanup',
        )
        parser.add_argument(
            '--skip-modules',
            action='store_true',
            help='Skip module mapping fixes',
        )
        parser.add_argument(
            '--skip-operations',
            action='store_true',
            help='Skip adding missing operations',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN MODE - No changes will be saved\n"))
        
        self.stdout.write(self.style.SUCCESS("="*80))
        self.stdout.write(self.style.SUCCESS("API ENDPOINT CLEANUP"))
        self.stdout.write(self.style.SUCCESS("="*80 + "\n"))

        # Statistics
        self.stats = {
            'paths_cleaned': 0,
            'modules_fixed': 0,
            'operations_added': 0,
            'format_suffixes_removed': 0,
            'actions_removed': 0,
        }

        try:
            with transaction.atomic():
                # Step 1: Clean up paths
                if not options['skip_paths']:
                    self._clean_paths()
                
                # Step 2: Fix module mappings
                if not options['skip_modules']:
                    self._fix_module_mappings()
                
                # Step 3: Add missing operations
                if not options['skip_operations']:
                    self._add_missing_operations()
                
                # Step 4: Remove unused action
                self._remove_unused_actions()
                
                if self.dry_run:
                    raise Exception("Dry run - rolling back transaction")
                
        except Exception as e:
            if self.dry_run:
                self.stdout.write(self.style.WARNING("\n✓ Dry run completed - no changes saved"))
            else:
                self.stdout.write(self.style.ERROR(f"\n✗ Error: {e}"))
                raise
        
        # Print summary
        self._print_summary()

    def _clean_paths(self):
        """Remove regex patterns from endpoint paths"""
        self.stdout.write(self.style.SUCCESS("\n📝 Step 1: Cleaning endpoint paths"))
        self.stdout.write("-" * 80)
        
        endpoints = ApiEndpoint.objects.all()
        
        for endpoint in endpoints:
            original_path = endpoint.path
            cleaned_path = self._clean_path(original_path)
            
            if cleaned_path != original_path:
                self.stdout.write(
                    f"  {self.style.WARNING('CLEAN')}: {original_path}\n"
                    f"      → {cleaned_path}"
                )
                endpoint.path = cleaned_path
                
                if not self.dry_run:
                    endpoint.save()
                
                self.stats['paths_cleaned'] += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Cleaned {self.stats['paths_cleaned']} paths")
        )

    def _clean_path(self, path):
        """Convert regex path to clean REST path"""
        # Remove leading /api/^ if present
        if '/^' in path:
            path = path.replace('/^', '/')
        
        # Replace (?P<pk>[^/.]+) with {id}
        path = re.sub(r'\(\?P<pk>\[.*?\]\+?\)', '{id}', path)
        
        # Replace (?P<format>[a-z0-9]+) patterns - remove format suffix endpoints
        path = re.sub(r'\\\.?\(\?P<format>\[.*?\]\+?\)/?\$?', '', path)
        
        # Remove trailing regex patterns
        path = re.sub(r'/?\$+$', '/', path)
        path = re.sub(r'/\$$', '/', path)
        
        # Ensure trailing slash
        if not path.endswith('/') and path != '/':
            path += '/'
        
        # Clean double slashes
        path = re.sub(r'/+', '/', path)
        
        return path

    def _fix_module_mappings(self):
        """Fix incorrect module/submodule mappings"""
        self.stdout.write(self.style.SUCCESS("\n🔧 Step 2: Fixing module mappings"))
        self.stdout.write("-" * 80)
        
        # Fix: Organizations should be CRM/ORGS not OPS/REPORTS
        try:
            crm_module = Module.objects.get(code='CRM')
            
            # Create ORGS submodule if it doesn't exist
            orgs_submodule, created = SubModule.objects.get_or_create(
                code='ORGS',
                defaults={'name': 'Organizations'}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Created SubModule: ORGS (Organizations)")
                )
            
            # Find organization endpoints
            org_endpoints = ApiEndpoint.objects.filter(
                path__icontains='organizations'
            )
            
            for endpoint in org_endpoints:
                old_module = endpoint.module.code if endpoint.module else 'NULL'
                old_submodule = endpoint.submodule.code if endpoint.submodule else 'NULL'
                
                endpoint.module = crm_module
                endpoint.submodule = orgs_submodule
                
                if not self.dry_run:
                    endpoint.save()
                
                self.stdout.write(
                    f"  {self.style.WARNING('FIX')}: {endpoint.path}\n"
                    f"      {old_module}/{old_submodule} → CRM/ORGS"
                )
                self.stats['modules_fixed'] += 1
        
        except Module.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("  ✗ CRM module not found - skipping")
            )
        
        # Fix: Empty module cleanup
        empty_module_endpoints = ApiEndpoint.objects.filter(module__code='')
        if empty_module_endpoints.exists():
            self.stdout.write(
                self.style.WARNING(f"\n  ⚠ Found {empty_module_endpoints.count()} endpoints with empty module")
            )
            # These should be manually reviewed
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Fixed {self.stats['modules_fixed']} module mappings")
        )

    def _add_missing_operations(self):
        """Add missing UPDATE and DELETE operations where appropriate"""
        self.stdout.write(self.style.SUCCESS("\n➕ Step 3: Adding missing operations"))
        self.stdout.write("-" * 80)
        
        # Get or create UPDATE and DELETE actions
        update_action, _ = Action.objects.get_or_create(code='update')
        delete_action, _ = Action.objects.get_or_create(code='delete')
        
        # Find detail endpoints (containing {id})
        all_endpoints = ApiEndpoint.objects.all()
        
        for endpoint in all_endpoints:
            path = endpoint.path
            
            # Skip if not a detail endpoint or if it's a custom action
            if '{id}' not in path:
                continue
            
            # Check if it's a custom action endpoint (e.g., /api/enquiries/{id}/close/)
            path_parts = path.rstrip('/').split('/')
            if len(path_parts) > 0 and path_parts[-1] not in ['{id}', 'id}']:
                # This is a custom action endpoint like /enquiries/{id}/close/
                continue
            
            # This is a standard detail endpoint like /api/enquiries/{id}/
            # Add PUT/PATCH (update) operation
            put_op, put_created = ApiOperation.objects.get_or_create(
                endpoint=endpoint,
                http_method='PUT',
                defaults={
                    'action': update_action,
                    'is_enabled': True,
                }
            )
            
            if put_created:
                self.stdout.write(
                    f"  {self.style.SUCCESS('ADD')}: PUT {path} → update"
                )
                self.stats['operations_added'] += 1
            
            patch_op, patch_created = ApiOperation.objects.get_or_create(
                endpoint=endpoint,
                http_method='PATCH',
                defaults={
                    'action': update_action,
                    'is_enabled': True,
                }
            )
            
            if patch_created:
                self.stdout.write(
                    f"  {self.style.SUCCESS('ADD')}: PATCH {path} → update"
                )
                self.stats['operations_added'] += 1
            
            # Add DELETE operation
            delete_op, delete_created = ApiOperation.objects.get_or_create(
                endpoint=endpoint,
                http_method='DELETE',
                defaults={
                    'action': delete_action,
                    'is_enabled': True,
                }
            )
            
            if delete_created:
                self.stdout.write(
                    f"  {self.style.SUCCESS('ADD')}: DELETE {path} → delete"
                )
                self.stats['operations_added'] += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Added {self.stats['operations_added']} operations")
        )

    def _remove_unused_actions(self):
        """Remove unused 'read' action if it exists"""
        self.stdout.write(self.style.SUCCESS("\n🗑️  Step 4: Removing unused actions"))
        self.stdout.write("-" * 80)
        
        try:
            read_action = Action.objects.get(code='read')
            
            # Check if it's used
            usage_count = ApiOperation.objects.filter(action=read_action).count()
            
            if usage_count == 0:
                self.stdout.write(
                    f"  {self.style.WARNING('REMOVE')}: Action 'read' (unused)"
                )
                
                if not self.dry_run:
                    read_action.delete()
                
                self.stats['actions_removed'] += 1
            else:
                self.stdout.write(
                    f"  ⚠ Action 'read' is used by {usage_count} operations - keeping it"
                )
        
        except Action.DoesNotExist:
            self.stdout.write("  ✓ Action 'read' does not exist")
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Removed {self.stats['actions_removed']} unused actions")
        )

    def _print_summary(self):
        """Print cleanup summary"""
        self.stdout.write(self.style.SUCCESS("\n" + "="*80))
        self.stdout.write(self.style.SUCCESS("CLEANUP SUMMARY"))
        self.stdout.write(self.style.SUCCESS("="*80))
        
        self.stdout.write(f"\n  Paths cleaned:        {self.stats['paths_cleaned']}")
        self.stdout.write(f"  Modules fixed:        {self.stats['modules_fixed']}")
        self.stdout.write(f"  Operations added:     {self.stats['operations_added']}")
        self.stdout.write(f"  Actions removed:      {self.stats['actions_removed']}")
        
        total_changes = sum(self.stats.values())
        self.stdout.write(self.style.SUCCESS(f"\n  Total changes:        {total_changes}\n"))
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("  ⚠ DRY RUN - No changes were saved\n"))
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ All changes saved successfully\n"))
