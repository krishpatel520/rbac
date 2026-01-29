from django.test import TestCase
from django.core.exceptions import PermissionDenied

from core.models import Tenant, Module, TenantModule
from accounts.models import User
from enquiry.services import EnquiryService


class TestEnquiryPermissions(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A")

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
            username="no_roles",
            password="password",
            tenant=self.tenant,
        )

    def test_user_without_permission_cannot_create(self):
        with self.assertRaises(PermissionDenied):
            EnquiryService.create_enquiry(
                user=self.user,
                customer_name="X",
                customer_email="x@example.com",
                subject="Fail",
            )
