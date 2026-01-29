from django.test import TestCase
from django.core.exceptions import PermissionDenied

from core.models import (
    Tenant, Role, Permission, RolePermission,
    Module, TenantModule
)
from accounts.models import User, UserRole
from enquiry.services import EnquiryService
from followup.services import FollowUpService
from followup.models import FollowUpStatus


class TestFollowUpLifecycle(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A")

        enquiry_module, _ = Module.objects.get_or_create(
            code="enquiry",
            defaults={"name": "Enquiry"},
        )
        followup_module, _ = Module.objects.get_or_create(
            code="followup",
            defaults={"name": "Followup"},
        )

        TenantModule.objects.create(
            tenant=self.tenant,
            module=enquiry_module,
            is_enabled=True,
        )
        TenantModule.objects.create(
            tenant=self.tenant,
            module=followup_module,
            is_enabled=True,
        )

        self.user = User.objects.create_user(
            username="orgadmin",
            password="password",
            tenant=self.tenant,
        )

        role, _ = Role.objects.get_or_create(name="OrgAdmin")

        permission_codes = [
            "enquiry.create",
            "enquiry.qualify",
            "followup.create",
            "followup.complete",
            "followup.cancel",
        ]

        for code in permission_codes:
            perm, _ = Permission.objects.get_or_create(code=code)
            RolePermission.objects.create(
                role=role,
                permission=perm,
                allowed=True,
            )

        UserRole.objects.create(user=self.user, role=role)

        self.enquiry = EnquiryService.create_enquiry(
            user=self.user,
            customer_name="Test",
            customer_email="test@example.com",
            subject="Test",
        )
        self.enquiry = EnquiryService.qualify(self.user, self.enquiry)

    def test_followup_complete(self):
        followup = FollowUpService.create_followup(
            user=self.user,
            enquiry=self.enquiry,
            note="Call back",
        )
        self.assertEqual(followup.status, FollowUpStatus.PENDING)

        followup = FollowUpService.complete(self.user, followup)
        self.assertEqual(followup.status, FollowUpStatus.COMPLETED)

    def test_cannot_cancel_after_complete(self):
        followup = FollowUpService.create_followup(
            user=self.user,
            enquiry=self.enquiry,
        )
        followup = FollowUpService.complete(self.user, followup)

        with self.assertRaises(PermissionDenied):
            FollowUpService.cancel(self.user, followup)
