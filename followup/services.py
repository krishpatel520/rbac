from __future__ import annotations

from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError

from followup.models import FollowUp, FollowUpStatus
from enquiry.models import Enquiry, EnquiryStatus
from core.models import TenantModule


class FollowUpService:
    """
    Domain service owning the FollowUp lifecycle.

    Lifecycle:
        PENDING → COMPLETED
        PENDING → CANCELED
    """

    # ─────────────────────────────
    # INTERNAL GUARDS
    # ─────────────────────────────



    @staticmethod
    def _check_tenant(user, followup: FollowUp | None):
        if followup and followup.tenant_id != user.tenant_id:
            raise PermissionDenied("Cross-tenant access denied")



    @staticmethod
    def _check_enquiry(enquiry: Enquiry, user):
        # Enquiry must belong to the same tenant
        if enquiry.tenant_id != user.tenant_id:
            raise PermissionDenied("Cross-tenant enquiry access denied")

        # Business rule:
        # Followups can only be created for QUALIFIED enquiries
        if enquiry.status != EnquiryStatus.QUALIFIED:
            raise PermissionDenied(
                "Followups can only be created for QUALIFIED enquiries"
            )

    # ─────────────────────────────
    # COMMANDS
    # ─────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_followup(
        user,
        *,
        enquiry: Enquiry,
        note: str = "",
    ):
        """
        Create a new FollowUp in PENDING state.

        Guards:
        - followup.create permission
        - followup module enabled
        - enquiry is QUALIFIED
        - enquiry belongs to user's tenant
        """


        FollowUpService._check_enquiry(enquiry, user)

        return FollowUp.objects.create(
            tenant=user.tenant,
            enquiry=enquiry,
            note=note,
            status=FollowUpStatus.PENDING,
        )

    @staticmethod
    @transaction.atomic
    def complete(user, followup: FollowUp):
        """
        Transition:
            PENDING → COMPLETED
        """
        FollowUpService._check_tenant(user, followup)
        
        # State validation: Only PENDING followups can be completed
        if followup.status != FollowUpStatus.PENDING:
            raise ValidationError(
                f"Cannot complete followup in '{followup.status}' status. "
                f"Only PENDING followups can be completed."
            )

        followup.status = FollowUpStatus.COMPLETED
        followup.save(update_fields=["status"])
        return followup

    @staticmethod
    @transaction.atomic
    def cancel(user, followup: FollowUp):
        """
        Transition:
            PENDING → CANCELED
        """
        FollowUpService._check_tenant(user, followup)
        
        # State validation: Only PENDING followups can be canceled
        if followup.status != FollowUpStatus.PENDING:
            raise ValidationError(
                f"Cannot cancel followup in '{followup.status}' status. "
                f"Only PENDING followups can be canceled."
            )

        followup.status = FollowUpStatus.CANCELED
        followup.save(update_fields=["status"])
        return followup
