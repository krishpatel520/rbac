from django.test import TestCase
from django.core.exceptions import PermissionDenied

from core.models import (
    Tenant, Role, Permission, RolePermission,
    Module, TenantModule
)
from accounts.models import User, UserRole
from enquiry.services import EnquiryService
from enquiry.models import EnquiryStatus


class TestEnquiryLifecycle(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")

        enquiry_module, _ = Module.objects.get_or_create(
            code="enquiry",
            defaults={"name": "Enquiry"},
        )
        TenantModule.objects.create(
            tenant=self.tenant,
            module=enquiry_module,
            is_enabled=True,
        )

        self.user = User.objects.create_user(
            username="sales",
            password="password",
            tenant=self.tenant,
        )

        role, _ = Role.objects.get_or_create(name="Sales")

        permission_codes = [
            "enquiry.create",
            "enquiry.qualify",
            "enquiry.disqualify",
            "enquiry.close",
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
        enquiry = EnquiryService.create_enquiry(
            user=self.user,
            customer_name="Alice",
            customer_email="alice@example.com",
            subject="Test",
        )
        self.assertEqual(enquiry.status, EnquiryStatus.NEW)

        enquiry = EnquiryService.qualify(self.user, enquiry)
        self.assertEqual(enquiry.status, EnquiryStatus.QUALIFIED)

        enquiry = EnquiryService.close(self.user, enquiry)
        self.assertEqual(enquiry.status, EnquiryStatus.CLOSED)

    def test_invalid_transition_new_to_close(self):
        enquiry = EnquiryService.create_enquiry(
            user=self.user,
            customer_name="Bob",
            customer_email="bob@example.com",
            subject="Invalid",
        )

        with self.assertRaises(PermissionDenied):
            EnquiryService.close(self.user, enquiry)
