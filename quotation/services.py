from __future__ import annotations

from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError

from quotation.models import Quotation, QuotationStatus
from enquiry.models import Enquiry, EnquiryStatus
from core.models import TenantModule


class QuotationService:
    """
    Domain service owning the Quotation lifecycle.

    Lifecycle:
        DRAFT → SENT
        SENT → ACCEPTED or REJECTED or EXPIRED
    """

    # ─────────────────────────────
    # INTERNAL GUARDS
    # ─────────────────────────────



    @staticmethod
    def _check_tenant(user, quotation: Quotation | None):
        if quotation and quotation.tenant_id != user.tenant_id:
            raise PermissionDenied("Cross-tenant access denied")



    @staticmethod
    def _check_enquiry(enquiry: Enquiry, user):
        # Enquiry must belong to the same tenant
        if enquiry.tenant_id != user.tenant_id:
            raise PermissionDenied("Cross-tenant enquiry access denied")

        # Business rule:
        # Quotations can only be created for QUALIFIED enquiries
        if enquiry.status != EnquiryStatus.QUALIFIED:
            raise PermissionDenied(
                "Quotations can only be created for QUALIFIED enquiries"
            )

    @staticmethod
    def _check_existing_quotation(enquiry: Enquiry):
        if hasattr(enquiry, "quotation"):
            raise PermissionDenied("Quotation already exists for this enquiry")

    # ─────────────────────────────
    # COMMANDS
    # ─────────────────────────────

    @staticmethod
    @transaction.atomic
    def create(
        user,
        *,
        enquiry: Enquiry,
        amount,
    ):
        """
        Create a new Quotation in DRAFT state.

        Guards:
        - quotation.create permission
        - quotation module enabled
        - enquiry is QUALIFIED
        - enquiry belongs to user's tenant
        - only one quotation per enquiry
        """


        QuotationService._check_enquiry(enquiry, user)
        QuotationService._check_existing_quotation(enquiry)

        return Quotation.objects.create(
            tenant=user.tenant,
            enquiry=enquiry,
            amount=amount,
            status=QuotationStatus.DRAFT,
        )

    @staticmethod
    @transaction.atomic
    def update(user, quotation: Quotation, **fields):
        """
        Update quotation fields (amount, etc).

        Allowed only in DRAFT or SENT.
        """
        QuotationService._check_tenant(user, quotation)

        for field, value in fields.items():
            setattr(quotation, field, value)

        quotation.save()
        return quotation

    @staticmethod
    @transaction.atomic
    def send(user, quotation: Quotation):
        """
        Transition:
            DRAFT → SENT
        """
        QuotationService._check_tenant(user, quotation)
        
        # State validation: Only DRAFT quotations can be sent
        if quotation.status != QuotationStatus.DRAFT:
            raise ValidationError(
                f"Cannot send quotation in '{quotation.status}' status. "
                f"Only DRAFT quotations can be sent."
            )

        quotation.status = QuotationStatus.SENT
        quotation.save(update_fields=["status"])
        return quotation

    @staticmethod
    @transaction.atomic
    def accept(user, quotation: Quotation):
        """
        Transition:
            SENT → ACCEPTED
        """
        QuotationService._check_tenant(user, quotation)
        
        # State validation: Only SENT quotations can be accepted
        if quotation.status != QuotationStatus.SENT:
            raise ValidationError(
                f"Cannot accept quotation in '{quotation.status}' status. "
                f"Only SENT quotations can be accepted."
            )

        quotation.status = QuotationStatus.ACCEPTED
        quotation.save(update_fields=["status"])
        return quotation

    @staticmethod
    @transaction.atomic
    def reject(user, quotation: Quotation):
        """
        Transition:
            SENT → REJECTED
        """
        QuotationService._check_tenant(user, quotation)
        
        # State validation: Only SENT quotations can be rejected
        if quotation.status != QuotationStatus.SENT:
            raise ValidationError(
                f"Cannot reject quotation in '{quotation.status}' status. "
                f"Only SENT quotations can be rejected."
            )

        quotation.status = QuotationStatus.REJECTED
        quotation.save(update_fields=["status"])
        return quotation

    @staticmethod
    @transaction.atomic
    def expire(user, quotation: Quotation):
        """
        Transition:
            SENT → EXPIRED

        Used when the organization terminates a quotation.
        """
        QuotationService._check_tenant(user, quotation)
        
        # State validation: Only SENT quotations can be expired
        if quotation.status != QuotationStatus.SENT:
            raise ValidationError(
                f"Cannot expire quotation in '{quotation.status}' status. "
                f"Only SENT quotations can be expired."
            )

        quotation.status = QuotationStatus.EXPIRED
        quotation.save(update_fields=["status"])
        return quotation
