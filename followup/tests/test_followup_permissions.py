from django.test import TestCase
from django.core.exceptions import PermissionDenied

from core.models import Tenant, Module, TenantModule
from accounts.models import User
from followup.services import FollowUpService


class TestFollowUpPermissions(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A")

        followup_module, _ = Module.objects.get_or_create(
            code="followup",
            defaults={"name": "Followup"},
        )
        TenantModule.objects.create(
            tenant=self.tenant,
            module=followup_module,
            is_enabled=True,
        )

        self.user = User.objects.create_user(
            username="sales",
            password="password",
            tenant=self.tenant,
        )

    def test_user_without_permission_cannot_complete(self):
        with self.assertRaises(PermissionDenied):
            FollowUpService.complete(self.user, None)
