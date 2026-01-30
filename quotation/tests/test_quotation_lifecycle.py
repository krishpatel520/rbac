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

from quotation.models import QuotationStatus


class TestQuotationLifecycle(TestCase):

    def setUp(self):
        # Tenant
        self.tenant = Tenant.objects.create(name="Tenant A")

        # Modules
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

        # Permissions
        enquiry_create = Permission.objects.create(code="enquiry.create")
        enquiry_qualify = Permission.objects.create(code="enquiry.qualify")

        quotation_create = Permission.objects.create(code="quotation.create")
        quotation_send = Permission.objects.create(code="quotation.send")
        quotation_accept = Permission.objects.create(code="quotation.accept")
        quotation_reject = Permission.objects.create(code="quotation.reject")
        quotation_expire = Permission.objects.create(code="quotation.expire")

        # Role
        role = Role.objects.create(name="OrgAdmin")

        RolePermission.objects.bulk_create([
            RolePermission(role=role, permission=enquiry_create),
            RolePermission(role=role, permission=enquiry_qualify),
            RolePermission(role=role, permission=quotation_create),
            RolePermission(role=role, permission=quotation_send),
            RolePermission(role=role, permission=quotation_accept),
            RolePermission(role=role, permission=quotation_reject),
            RolePermission(role=role, permission=quotation_expire),
        ])

        # User
        self.user = User.objects.create_user(
            username="orgadmin",
            password="password",
            tenant=self.tenant,
        )
        UserRole.objects.create(user=self.user, role=role)

        # Qualified enquiry
        self.enquiry = EnquiryService.create_enquiry(
            user=self.user,
            customer_name="Alice",
            customer_email="alice@example.com",
            subject="Quotation Test",
        )
        self.enquiry = EnquiryService.qualify(self.user, self.enquiry)

    def test_valid_lifecycle(self):
        quotation = QuotationService.create(
            user=self.user,
            enquiry=self.enquiry,
            amount=1000,
        )
        self.assertEqual(quotation.status, QuotationStatus.DRAFT)

        quotation = QuotationService.send(self.user, quotation)
        self.assertEqual(quotation.status, QuotationStatus.SENT)

        quotation = QuotationService.accept(self.user, quotation)
        self.assertEqual(quotation.status, QuotationStatus.ACCEPTED)

    def test_invalid_transition_draft_to_accept(self):
        quotation = QuotationService.create(
            user=self.user,
            enquiry=self.enquiry,
            amount=500,
        )

        with self.assertRaises(PermissionDenied):
            QuotationService.accept(self.user, quotation)

    def test_sent_to_rejected(self):
        quotation = QuotationService.create(
            user=self.user,
            enquiry=self.enquiry,
            amount=700,
        )
        quotation = QuotationService.send(self.user, quotation)

        quotation = QuotationService.reject(self.user, quotation)
        self.assertEqual(quotation.status, QuotationStatus.REJECTED)

    def test_sent_to_expired(self):
        quotation = QuotationService.create(
            user=self.user,
            enquiry=self.enquiry,
            amount=900,
        )
        quotation = QuotationService.send(self.user, quotation)

        quotation = QuotationService.expire(self.user, quotation)
        self.assertEqual(quotation.status, QuotationStatus.EXPIRED)
