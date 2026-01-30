from django.test import TestCase
from django.core.exceptions import PermissionDenied

from core.models import Tenant, Module, TenantModule
from accounts.models import User
from organization.services import OrganizationService


class TestOrganizationPermissions(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A")
        self.organization = self.tenant.profile

        org_module, _ = Module.objects.get_or_create(
            code="organization",
            defaults={"name": "Organization"},
        )
        TenantModule.objects.create(
            tenant=self.tenant,
            module=org_module,
            is_enabled=True,
        )

        # User with NO organization permissions
        self.user = User.objects.create_user(
            username="sales",
            password="password",
            tenant=self.tenant,
        )

    def test_user_without_permission_cannot_suspend(self):
        with self.assertRaises(PermissionDenied):
            OrganizationService.suspend(self.user, self.organization)
