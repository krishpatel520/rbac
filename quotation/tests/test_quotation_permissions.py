from django.test import TestCase
from django.core.exceptions import PermissionDenied

from core.models import (
    Tenant,
    Module,
    TenantModule,
    Role,
    Permission,
    RolePermission,
)
from accounts.models import User, UserRole

from enquiry.services import EnquiryService
from quotation.services import QuotationService


class TestQuotationPermissions(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant A")

        enquiry_module, _ = Module.objects.get_or_create(
            code="enquiry",
            defaults={"name": "Enquiry"},
        )
        quotation_module, _ = Module.objects.get_or_create(
            code="quotation",
            defaults={"name": "Quotation"},
        )

        TenantModule.objects.bulk_create([
            TenantModule(tenant=self.tenant, module=enquiry_module, is_enabled=True),
            TenantModule(tenant=self.tenant, module=quotation_module, is_enabled=True),
        ])

        # Only enquiry permissions, no quotation permissions
        enquiry_create = Permission.objects.create(code="enquiry.create")
        enquiry_qualify = Permission.objects.create(code="enquiry.qualify")

        role = Role.objects.create(name="SalesExecutive")

        RolePermission.objects.bulk_create([
            RolePermission(role=role, permission=enquiry_create),
            RolePermission(role=role, permission=enquiry_qualify),
        ])

        self.user = User.objects.create_user(
            username="sales",
            password="password",
            tenant=self.tenant,
        )
        UserRole.objects.create(user=self.user, role=role)

        self.enquiry = EnquiryService.create_enquiry(
            user=self.user,
            customer_name="Bob",
            customer_email="bob@example.com",
            subject="No Quotation Permission",
        )
        self.enquiry = EnquiryService.qualify(self.user, self.enquiry)

    def test_user_without_permission_cannot_create(self):
        with self.assertRaises(PermissionDenied):
            QuotationService.create(
                user=self.user,
                enquiry=self.enquiry,
                amount=1000,
            )
