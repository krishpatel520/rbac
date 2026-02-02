from __future__ import annotations

from django.db import transaction
from django.core.exceptions import PermissionDenied

from quotation.models import Quotation, QuotationStatus
from enquiry.models import Enquiry, EnquiryStatus
from core.services.rbac import has_permission
from core.services.rules import is_allowed
from core.models import TenantModule


class QuotationService:
    """
    Domain service owning the Quotation lifecycle.

    Lifecycle:
        DRAFT → SENT
        SENT  → ACCEPTED
        SENT  → REJECTED
        SENT  → EXPIRED
    """

    # ─────────────────────────────
    # INTERNAL GUARDS
    # ─────────────────────────────

    @staticmethod
    def _check_permission(user, permission_code, obj=None):
        if not has_permission(user, permission_code):
            raise PermissionDenied("RBAC denied")

        if not is_allowed(user, permission_code, obj):
            raise PermissionDenied("ABAC rule denied")

    @staticmethod
    def _check_tenant(user, quotation: Quotation | None):
        if quotation and quotation.tenant_id != user.tenant_id:
            raise PermissionDenied("Cross-tenant access denied")

    @staticmethod
    def _check_subscription(user, module_code="quotation"):
        return TenantModule.objects.filter(
            tenant=user.tenant,
            module__code=module_code,
            is_enabled=True,
        ).exists()

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
        QuotationService._check_permission(user, "quotation.create")

        if not QuotationService._check_subscription(user):
            raise PermissionDenied("Module not enabled")

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
        QuotationService._check_permission(user, "quotation.update", quotation)

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
        QuotationService._check_permission(user, "quotation.send", quotation)

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
        QuotationService._check_permission(user, "quotation.accept", quotation)

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
        QuotationService._check_permission(user, "quotation.reject", quotation)

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
        QuotationService._check_permission(user, "quotation.expire", quotation)

        quotation.status = QuotationStatus.EXPIRED
        quotation.save(update_fields=["status"])
        return quotation
