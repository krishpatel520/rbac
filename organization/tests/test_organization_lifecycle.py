from django.test import TestCase
from django.core.exceptions import PermissionDenied

from core.models import (
    Tenant, Role, Permission, RolePermission,
    Module, TenantModule
)
from accounts.models import User, UserRole
from organization.models import OrganizationStatus
from organization.services import OrganizationService


class TestOrganizationLifecycle(TestCase):

    def setUp(self):
        # Tenant implicitly creates OrganizationProfile
        self.tenant = Tenant.objects.create(name="Org Test Tenant")
        self.organization = self.tenant.profile

        # Enable organization module
        org_module, _ = Module.objects.get_or_create(
            code="organization",
            defaults={"name": "Organization"},
        )
        TenantModule.objects.create(
            tenant=self.tenant,
            module=org_module,
            is_enabled=True,
        )

        # Create OrgAdmin user
        self.user = User.objects.create_user(
            username="orgadmin",
            password="password",
            tenant=self.tenant,
        )

        role, _ = Role.objects.get_or_create(name="OrgAdmin")

        permission_codes = [
            "organization.update",
            "organization.suspend",
            "organization.activate",
            "organization.archive",
        ]

        for code in permission_codes:
            perm, _ = Permission.objects.get_or_create(code=code)
            RolePermission.objects.create(
                role=role,
                permission=perm,
                allowed=True,
            )

        UserRole.objects.create(user=self.user, role=role)

    def test_valid_lifecycle(self):
        self.assertEqual(self.organization.status, OrganizationStatus.ACTIVE)

        org = OrganizationService.suspend(self.user, self.organization)
        self.assertEqual(org.status, OrganizationStatus.SUSPENDED)

        org = OrganizationService.activate(self.user, org)
        self.assertEqual(org.status, OrganizationStatus.ACTIVE)

        org = OrganizationService.suspend(self.user, org)
        self.assertEqual(org.status, OrganizationStatus.SUSPENDED)

        org = OrganizationService.archive(self.user, org)
        self.assertEqual(org.status, OrganizationStatus.ARCHIVED)

    def test_invalid_activate_after_archive(self):
        org = OrganizationService.suspend(self.user, self.organization)
        org = OrganizationService.archive(self.user, org)

        with self.assertRaises(PermissionDenied):
            OrganizationService.activate(self.user, org)
