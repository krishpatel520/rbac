from django.db import transaction
from django.core.exceptions import PermissionDenied

from organization.models import OrganizationProfile, OrganizationStatus
from core.services.rbac import has_permission
from core.services.rules import is_allowed


class OrganizationService:
    """
    Domain service owning Organization lifecycle.

    Lifecycle:
        ACTIVE <-> SUSPENDED -> ARCHIVED
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
        OrganizationService._check_permission(user, "organization.update", org)

        for field, value in fields.items():
            setattr(org, field, value)

        org.save()
        return org

    @staticmethod
    @transaction.atomic
    def suspend(user, org: OrganizationProfile):
        """
        Transition:
            ACTIVE -> SUSPENDED
        """
        OrganizationService._check_tenant(user, org)
        OrganizationService._check_permission(user, "organization.suspend", org)

        org.status = OrganizationStatus.SUSPENDED
        org.save(update_fields=["status"])
        return org

    @staticmethod
    @transaction.atomic
    def activate(user, org: OrganizationProfile):
        """
        Transition:
            SUSPENDED -> ACTIVE
        """
        OrganizationService._check_tenant(user, org)
        OrganizationService._check_permission(user, "organization.activate", org)

        org.status = OrganizationStatus.ACTIVE
        org.save(update_fields=["status"])
        return org

    @staticmethod
    @transaction.atomic
    def archive(user, org: OrganizationProfile):
        """
        Transition:
            ACTIVE/SUSPENDED -> ARCHIVED
        """
        OrganizationService._check_tenant(user, org)
        OrganizationService._check_permission(user, "organization.archive", org)

        org.status = OrganizationStatus.ARCHIVED
        org.save(update_fields=["status"])
        return org
