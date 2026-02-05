from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError

from organization.models import OrganizationProfile, OrganizationStatus



class OrganizationService:
    """
    Domain service owning Organization lifecycle.

    Lifecycle:
        ACTIVE <-> ARCHIVED -> SUSPENDED
    """

    # ─────────────────────────────
    # INTERNAL GUARDS
    # ─────────────────────────────



    @staticmethod
    def _check_tenant(user, org: OrganizationProfile):
        """
        Prevent cross-tenant organization access.
        """
        if org.tenant_id != user.tenant_id:
            raise PermissionDenied("Cross-tenant access denied")

    # ─────────────────────────────
    # QUERIES
    # ─────────────────────────────

    @staticmethod
    def get_current_org(user) -> OrganizationProfile:
        """
        Returns the organization profile of the user's tenant.
        """
        try:
            return user.tenant.profile
        except OrganizationProfile.DoesNotExist:
            raise PermissionDenied("Organization profile missing")

    # ─────────────────────────────
    # COMMANDS (LIFECYCLE)
    # ─────────────────────────────

    @staticmethod
    @transaction.atomic
    def update(user, org: OrganizationProfile, **fields):
        """
        Update organization metadata.

        Allowed only when ACTIVE.
        """
        OrganizationService._check_tenant(user, org)

        for field, value in fields.items():
            setattr(org, field, value)

        org.save()
        return org

    @staticmethod
    @transaction.atomic
    def archive(user, org: OrganizationProfile):
        """
        Transition:
            ACTIVE → ARCHIVED
        """
        OrganizationService._check_tenant(user, org)
        
        # State validation: Only ACTIVE organizations can be archived
        if org.status != OrganizationStatus.ACTIVE:
            raise ValidationError(
                f"Cannot archive organization in '{org.status}' status. "
                f"Only ACTIVE organizations can be archived."
            )

        org.status = OrganizationStatus.ARCHIVED
        org.save(update_fields=["status"])
        return org

    @staticmethod
    @transaction.atomic
    def unarchive(user, org: OrganizationProfile):
        """
        Transition:
            ARCHIVED → ACTIVE
        """
        OrganizationService._check_tenant(user, org)
        
        # State validation: Only ARCHIVED organizations can be unarchived
        if org.status != OrganizationStatus.ARCHIVED:
            raise ValidationError(
                f"Cannot unarchive organization in '{org.status}' status. "
                f"Only ARCHIVED organizations can be unarchived."
            )

        org.status = OrganizationStatus.ACTIVE
        org.save(update_fields=["status"])
        return org

    @staticmethod
    @transaction.atomic
    def suspend(user, org: OrganizationProfile):
        """
        Transition:
            ARCHIVED → SUSPENDED
        """
        OrganizationService._check_tenant(user, org)
        
        # State validation: Only ARCHIVED organizations can be suspended
        if org.status != OrganizationStatus.ARCHIVED:
            raise ValidationError(
                f"Cannot suspend organization in '{org.status}' status. "
                f"Only ARCHIVED organizations can be suspended."
            )

        org.status = OrganizationStatus.SUSPENDED
        org.save(update_fields=["status"])
        return org
