from django.db import transaction
from django.core.exceptions import PermissionDenied

from enquiry.models import Enquiry, EnquiryStatus
from core.services.rbac import has_permission
from core.services.rules import is_allowed
from core.models import TenantModule


class EnquiryService:

    @staticmethod
    def _check_permission(user, permission_code, obj=None):
        if not has_permission(user, permission_code):
            raise PermissionDenied("RBAC denied")

        if not is_allowed(user, permission_code, obj):
            raise PermissionDenied("ABAC rule denied")

    @staticmethod
    def _check_tenant(user, enquiry: Enquiry | None):
        if enquiry and enquiry.tenant_id != user.tenant_id:
            raise PermissionDenied("Cross-tenant access denied")

    @staticmethod
    def _check_subscription(user, module_code="enquiry"):
        return TenantModule.objects.filter(
            tenant=user.tenant,
            module__code=module_code,
            is_enabled=True,
        ).exists()

    # ─────────────────────────────
    # COMMANDS
    # ─────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_enquiry(user, *, customer_name, customer_email, subject):
        EnquiryService._check_permission(user, "enquiry.create")

        if not EnquiryService._check_subscription(user):
            raise PermissionDenied("Module not enabled")

        return Enquiry.objects.create(
            tenant=user.tenant,
            customer_name=customer_name,
            customer_email=customer_email,
            subject=subject,
            status=EnquiryStatus.NEW,
        )

    @staticmethod
    @transaction.atomic
    def qualify(user, enquiry: Enquiry):
        EnquiryService._check_tenant(user, enquiry)
        EnquiryService._check_permission(user, "enquiry.qualify", enquiry)

        enquiry.status = EnquiryStatus.QUALIFIED
        enquiry.save(update_fields=["status"])
        return enquiry

    @staticmethod
    @transaction.atomic
    def disqualify(user, enquiry: Enquiry):
        EnquiryService._check_tenant(user, enquiry)
        EnquiryService._check_permission(user, "enquiry.disqualify", enquiry)

        enquiry.status = EnquiryStatus.DISQUALIFIED
        enquiry.save(update_fields=["status"])
        return enquiry

    @staticmethod
    @transaction.atomic
    def close(user, enquiry: Enquiry):
        EnquiryService._check_tenant(user, enquiry)
        EnquiryService._check_permission(user, "enquiry.close", enquiry)

        enquiry.status = EnquiryStatus.CLOSED
        enquiry.save(update_fields=["status"])
        return enquiry
