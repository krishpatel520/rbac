from __future__ import annotations

from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError

from enquiry.models import Enquiry, EnquiryStatus
from core.models import TenantModule


class EnquiryService:



    @staticmethod
    def _check_tenant(user, enquiry: Enquiry | None):
        if enquiry and enquiry.tenant_id != user.tenant_id:
            raise PermissionDenied("Cross-tenant access denied")



    # ─────────────────────────────
    # COMMANDS
    # ─────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_enquiry(user, *, customer_name, customer_email, subject):


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
        
        # State validation: Only NEW enquiries can be qualified
        if enquiry.status != EnquiryStatus.NEW:
            raise ValidationError(
                f"Cannot qualify enquiry in '{enquiry.status}' status. "
                f"Only NEW enquiries can be qualified."
            )

        enquiry.status = EnquiryStatus.QUALIFIED
        enquiry.save(update_fields=["status"])
        return enquiry

    @staticmethod
    @transaction.atomic
    def disqualify(user, enquiry: Enquiry):
        EnquiryService._check_tenant(user, enquiry)
        
        # State validation: Only NEW enquiries can be disqualified
        if enquiry.status != EnquiryStatus.NEW:
            raise ValidationError(
                f"Cannot disqualify enquiry in '{enquiry.status}' status. "
                f"Only NEW enquiries can be disqualified."
            )

        enquiry.status = EnquiryStatus.DISQUALIFIED
        enquiry.save(update_fields=["status"])
        return enquiry

    @staticmethod
    @transaction.atomic
    def close(user, enquiry: Enquiry):
        EnquiryService._check_tenant(user, enquiry)
        
        # State validation: Only QUALIFIED or DISQUALIFIED enquiries can be closed
        if enquiry.status not in [EnquiryStatus.QUALIFIED, EnquiryStatus.DISQUALIFIED]:
            raise ValidationError(
                f"Cannot close enquiry in '{enquiry.status}' status. "
                f"Only QUALIFIED or DISQUALIFIED enquiries can be closed."
            )

        enquiry.status = EnquiryStatus.CLOSED
        enquiry.save(update_fields=["status"])
        return enquiry
