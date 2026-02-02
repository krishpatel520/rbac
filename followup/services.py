from __future__ import annotations

from django.db import transaction
from django.core.exceptions import PermissionDenied

from followup.models import FollowUp, FollowUpStatus
from enquiry.models import Enquiry, EnquiryStatus
from core.services.rbac import has_permission
from core.services.rules import is_allowed
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
    def _check_permission(user, permission_code, obj=None):
        if not has_permission(user, permission_code):
            raise PermissionDenied("RBAC denied")

        if not is_allowed(user, permission_code, obj):
            raise PermissionDenied("ABAC rule denied")

    @staticmethod
    def _check_tenant(user, followup: FollowUp | None):
        if followup and followup.tenant_id != user.tenant_id:
            raise PermissionDenied("Cross-tenant access denied")

    @staticmethod
    def _check_subscription(user, module_code="followup"):
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
        FollowUpService._check_permission(user, "followup.create")

        if not FollowUpService._check_subscription(user):
            raise PermissionDenied("Module not enabled")

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
        FollowUpService._check_permission(user, "followup.complete", followup)

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
        FollowUpService._check_permission(user, "followup.cancel", followup)

        followup.status = FollowUpStatus.CANCELED
        followup.save(update_fields=["status"])
        return followup
