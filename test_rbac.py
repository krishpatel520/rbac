"""
Comprehensive RBAC End-to-End Testing Script
Tests tenant isolation, permission enforcement, and middleware flow
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rbac_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from core.services.RBACMiddleware import RBACMiddleware
from core.models import *
from accounts.models import *
from datetime import date, timedelta

User = get_user_model()
factory = RequestFactory()

# Test results tracking
results = {
    'passed': 0,
    'failed': 0,
    'errors': 0,
    'tests': []
}

def test_case(category, name, user, method, path, should_pass=True, expected_error=None):
    """
    Test a single RBAC check
    """
    global results
    
    print(f"\n{'='*80}")
    print(f"[{category}] {name}")
    print(f"{'='*80}")
    print(f"User: {user.username if user else 'Anonymous'} @ {user.tenant.name if user and user.tenant else 'N/A'}")
    print(f"Request: {method} {path}")
    print(f"Expected: {'PASS' if should_pass else 'FAIL'}")
    if expected_error:
        print(f"Expected Error: {expected_error}")
    
    # Create mock request
    method_map = {
        'GET': factory.get,
        'POST': factory.post,
        'PUT': factory.put,
        'DELETE': factory.delete,
        'OPTIONS': factory.options,
    }
    
    request = method_map.get(method, factory.get)(path)
    request.user = user if user else type('obj', (object,), {'is_authenticated': False})()
    
    # Create middleware instance
    def mock_get_response(req):
        return "SUCCESS"
    
    middleware = RBACMiddleware(mock_get_response)
    
    # Test
    test_result = {
        'category': category,
        'name': name,
        'user': user.username if user else 'Anonymous',
        'request': f"{method} {path}",
        'expected': 'PASS' if should_pass else 'FAIL',
        'actual': None,
        'status': None
    }
    
    try:
        result = middleware(request)
        test_result['actual'] = 'PASS'
        
        if should_pass:
            print(f"✓ PASS - Request allowed")
            test_result['status'] = 'PASSED'
            results['passed'] += 1
        else:
            print(f"✗ FAIL - Expected deny but request was allowed")
            test_result['status'] = 'FAILED'
            results['failed'] += 1
            
    except PermissionError as e:
        test_result['actual'] = f'DENY: {str(e)}'
        
        if not should_pass:
            if expected_error and expected_error not in str(e):
                print(f"⚠ PARTIAL - Denied but wrong error message")
                print(f"  Expected: {expected_error}")
                print(f"  Got: {e}")
                test_result['status'] = 'PARTIAL'
                results['failed'] += 1
            else:
                print(f"✓ PASS - Correctly denied: {e}")
                test_result['status'] = 'PASSED'
                results['passed'] += 1
        else:
            print(f"✗ FAIL - Unexpected deny: {e}")
            test_result['status'] = 'FAILED'
            results['failed'] += 1
            
    except Exception as e:
        test_result['actual'] = f'ERROR: {str(e)}'
        test_result['status'] = 'ERROR'
        print(f"✗ ERROR - {type(e).__name__}: {e}")
        results['errors'] += 1
    
    results['tests'].append(test_result)
    return test_result


# ============================================================
# SETUP
# ============================================================
print("\n" + "="*80)
print(" RBAC COMPREHENSIVE END-TO-END TESTING")
print("="*80)

# Get users
print("\nLoading test users...")
viewer_a = User.objects.get(username='viewer_a')  # TestTenant, Viewer
editor_a = User.objects.get(username='editor_a')  # TestTenant, Editor
viewer_b = User.objects.get(username='viewer_b')  # SecondTenant, Viewer
admin_b = User.objects.get(username='admin_b')    # SecondTenant, SuperAdmin

print(f"  ✓ viewer_a: {viewer_a.tenant.name}, Role: Viewer (4 permissions)")
print(f"  ✓ editor_a: {editor_a.tenant.name}, Role: Editor (12 permissions)")
print(f"  ✓ viewer_b: {viewer_b.tenant.name}, Role: Viewer (16 permissions)")
print(f"  ✓ admin_b: {admin_b.tenant.name}, Role: SuperAdmin (112 permissions)")

# Enable SYSTEM module for tenants (required for OPTIONS /api/)
print("Enabling SYSTEM module for tenants...")
system_module = Module.objects.filter(code='SYSTEM').first()

if system_module:
    for tenant in [viewer_a.tenant, viewer_b.tenant, admin_b.tenant]:
        if tenant:
            # Clean up potential duplicates first
            TenantModule.objects.filter(tenant=tenant, module=system_module).delete()
            
            # Create fresh subscription
            TenantModule.objects.create(
                tenant=tenant, 
                module=system_module,
                is_enabled=True, 
                expiration_date=date.today() + timedelta(days=365)
            )
            print(f"  ✓ Enabled SYSTEM for {tenant.name}")

# Grant SYSTEM permissions to SuperAdmin role (admin_b)
print("Granting SYSTEM permissions to SuperAdmin role...")
superadmin_role = Role.objects.filter(name='SuperAdmin', tenant=admin_b.tenant).first()
if superadmin_role and system_module:
    # Get the TenantModule for SYSTEM
    sys_tm = TenantModule.objects.filter(tenant=admin_b.tenant, module=system_module).first()
    
    if sys_tm:
        # Get all actions
        for action in Action.objects.all():
            perm, created = Permission.objects.get_or_create(
                tenant=admin_b.tenant,
                tenant_module=sys_tm,  # Correct FK
                action=action
            )
            RolePermission.objects.get_or_create(role=superadmin_role, permission=perm, defaults={'allowed': True})
        print(f"  ✓ Granted all SYSTEM actions to SuperAdmin")
    else:
        print("  ⚠ Could not find SYSTEM TenantModule for admin_b")

# ============================================================
# CATEGORY 1: Infrastructure Bypass Tests
# ============================================================
print("\n" + "="*80)
print(" CATEGORY 1: INFRASTRUCTURE BYPASS")
print("="*80)

test_case(
    "Infrastructure", 
    "Admin path should bypass RBAC",
    user=viewer_a,
    method='GET',
    path='/admin/',
    should_pass=True
)

test_case(
    "Infrastructure",
    "Static path should bypass RBAC",
    user=viewer_a,
    method='GET',
    path='/static/css/style.css',
    should_pass=True
)

test_case(
    "Infrastructure",
    "Media path should bypass RBAC",
    user=viewer_a,
    method='GET',
    path='/media/uploads/file.pdf',
    should_pass=True
)

# ============================================================
# CATEGORY 2: Anonymous User Bypass
# ============================================================
print("\n" + "="*80)
print(" CATEGORY 2: ANONYMOUS USER BYPASS")
print("="*80)

test_case(
    "Anonymous",
    "Anonymous user should bypass middleware",
    user=None,
    method='GET',
    path='/api/enquiries/',
    should_pass=True
)

# ============================================================
# CATEGORY 3: API Operation Resolution
# ============================================================
print("\n" + "="*80)
print(" CATEGORY 3: API OPERATION RESOLUTION")
print("="*80)

test_case(
    "API Resolution",
    "Registered API should resolve",
    user=viewer_a,
    method='GET',
    path='/api/^enquiries/$',
    should_pass=True  # Has permission, so should PASS entirely
)

test_case(
    "API Resolution",
    "Unregistered API should fail at resolution",
    user=viewer_a,
    method='GET',
    path='/api/completely-unknown-endpoint/',
    should_pass=False,
    expected_error="API not registered"
)


# ============================================================
# CATEGORY 3.5: Tenant Subscription Validation (NEW)
# ============================================================
print("\n" + "="*80)
print(" CATEGORY 3.5: TENANT SUBSCRIPTION VALIDATION")
print("="*80)

# 1. Disable Crm/Leads for TestTenant (viewer_a's tenant)
print("Disabling Crm/Leads for TestTenant...")
test_tenant = Tenant.objects.get(name='TestTenant')
crm_leads = TenantModule.objects.filter(
    tenant=test_tenant, 
    module__code='CRM', 
    submodule__code='LEADS'
).first()

if crm_leads:
    original_state = crm_leads.is_enabled
    crm_leads.is_enabled = False
    crm_leads.save()

    # 2. Test Access - Should FAIL
    test_case(
        "Tenant Subscription",
        "User should BE BLOCKED when tenant module is disabled",
        user=viewer_a,
        method='GET',
        path='/api/^enquiries/$', # Crm/Leads
        should_pass=False,
        expected_error="Module/Submodule disabled for tenant"
    )

    # 3. Re-enable
    print("Re-enabling Crm/Leads for TestTenant...")
    crm_leads.is_enabled = original_state
    crm_leads.save()
    
    # 4. Test Access - Should PASS
    test_case(
        "Tenant Subscription",
        "User should HAVE ACCESS when tenant module is enabled",
        user=viewer_a,
        method='GET',
        path='/api/^enquiries/$',
        should_pass=True
    )
else:
    print("⚠ SKIPPING: TenantModule for CRM/LEADS not found for TestTenant")

# ============================================================
# CATEGORY 4: Permission-Based Access Control
# ============================================================
print("\n" + "="*80)
print(" CATEGORY 4: PERMISSION-BASED ACCESS CONTROL")
print("="*80)

# viewer_a permissions: Crm/Leads:view, Crm/Deals:view, Ops/Tasks:view, Ops/Reports:view

test_case(
    "Permissions",
    "Viewer CAN view (Crm/Leads)",
    user=viewer_a,
    method='GET',
    path='/api/^enquiries/$',  # Mapped to Crm/Leads
    should_pass=True
)

test_case(
    "Permissions",
    "Viewer CANNOT create (Crm/Leads)",
    user=viewer_a,
    method='POST',
    path='/api/^enquiries/$',
    should_pass=False,
    expected_error="Permission denied"
)

test_case(
    "Permissions",
    "Viewer CAN view (Crm/Deals)",
    user=viewer_a,
    method='GET',
    path='/api/^quotations/$',  # Mapped to Crm/Deals
    should_pass=True
)

test_case(
    "Permissions",
    "Viewer CANNOT create (Crm/Deals)",
    user=viewer_a,
    method='POST',
    path='/api/^quotations/$',
    should_pass=False,
    expected_error="Permission denied"
)

# editor_a permissions: view, create, update (no delete)

test_case(
    "Permissions",
    "Editor CAN view",
    user=editor_a,
    method='GET',
    path='/api/^enquiries/$',
    should_pass=True
)

test_case(
    "Permissions",
    "Editor CAN create",
    user=editor_a,
    method='POST',
    path='/api/^enquiries/$',
    should_pass=True
)

# Note: We don't have DELETE operations registered, so can't test editor_a DELETE denial

# admin_b has full permissions

test_case(
    "Permissions",
    "SuperAdmin CAN view",
    user=admin_b,
    method='GET',
    path='/api/^enquiries/$',
    should_pass=True
)

test_case(
    "Permissions",
    "SuperAdmin CAN create",
    user=admin_b,
    method='POST',
    path='/api/^enquiries/$',
    should_pass=True
)

# ============================================================
# CATEGORY 5: Cross-Tenant Access Verification
# ============================================================
print("\n" + "="*80)
print(" CATEGORY 5: TENANT ISOLATION")
print("="*80)

# viewer_a (TestTenant) has Crm/Leads:view permission
# viewer_b (SecondTenant) also has permissions but different tenant

test_case(
    "Tenant Isolation",
    "User from TestTenant can access with valid permissions",
    user=viewer_a,
    method='GET',
    path='/api/^enquiries/$',
    should_pass=True
)

test_case(
    "Tenant Isolation",
    "User from SecondTenant can access with valid permissions",
    user=viewer_b,
    method='GET',
    path='/api/^enquiries/$',
    should_pass=True  # Both tenants have Crm/Leads enabled
)

# Note: True tenant isolation happens at the data layer (ORM queries filter by tenant)
# RBAC just checks if the user has permission to access the endpoint

# ============================================================
# CATEGORY 6: Module Hierarchy Testing
# ============================================================
print("\n" + "="*80)
print(" CATEGORY 6: MODULE/SUBMODULE HIERARCHY")
print("="*80)

# Test that submodule permission works
test_case(
    "Hierarchy",
    "Permission at submodule level should work",
    user=viewer_a,  # Has Crm/Leads:view
    method='GET',
    path='/api/^enquiries/$',  # Endpoint is Crm/Leads  
    should_pass=True
)

# ============================================================
# CATEGORY 7: Edge Cases
# ============================================================
print("\n" + "="*80)
print(" CATEGORY 7: EDGE CASES")
print("="*80)

# Test OPTIONS method (CORS)
test_case(
    "Edge Cases",
    "OPTIONS request should work if user has options permission",
    user=admin_b,  # SuperAdmin has 'options' permission
    method='OPTIONS',
    path='/api/',
    should_pass=True
)

test_case(
    "Edge Cases",
    "OPTIONS without permission should fail",
    user=viewer_a,  # Viewer doesn't have 'options' permission
    method='OPTIONS',
    path='/api/',
    should_pass=False,
    expected_error="Permission denied"
)

# ============================================================
# RESULTS SUMMARY
# ============================================================
print("\n" + "="*80)
print(" TEST RESULTS SUMMARY")  
print("="*80)

total_tests = results['passed'] + results['failed'] + results['errors']
pass_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0

print(f"\nTotal Tests: {total_tests}")
print(f"Passed: {results['passed']} ({pass_rate:.1f}%)")
print(f"Failed: {results['failed']}")
print(f"Errors: {results['errors']}")

if results['failed'] > 0 or results['errors'] > 0:
    print(f"\n❌ FAILED TESTS:")
    for test in results['tests']:
        if test['status'] in ['FAILED', 'ERROR', 'PARTIAL']:
            print(f"  - [{test['category']}] {test['name']}")
            print(f"    Expected: {test['expected']}, Got: {test['actual']}")

print("\n" + "="*80)
if results['failed'] == 0 and results['errors'] == 0:
    print("✓ ALL TESTS PASSED!")
else:
    print(f"⚠ {results['failed'] + results['errors']} TESTS FAILED")
print("="*80 + "\n")

# Save detailed results
with open('test_results.txt', 'w', encoding='utf-8') as f:
    f.write("RBAC END-TO-END TEST RESULTS\n")
    f.write("="*80 + "\n\n")
    
    for test in results['tests']:
        f.write(f"[{test['status']}] {test['category']} - {test['name']}\n")
        f.write(f"  User: {test['user']}\n")
        f.write(f"  Request: {test['request']}\n")
        f.write(f"  Expected: {test['expected']}\n")
        f.write(f"  Actual: {test['actual']}\n")
        f.write("\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write(f"SUMMARY: {results['passed']}/{total_tests} passed ({pass_rate:.1f}%)\n")
    f.write("="*80 + "\n")

print("Detailed results saved to test_results.txt")
