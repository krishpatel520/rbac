from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from organization.models import OrganizationProfile
from organization.services import OrganizationService
from organization.api.serializers import OrganizationSerializer


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Organization lifecycle management.

    - No create endpoint (organizations are auto-created per tenant)
    - Tenant-scoped access
    - Superusers can see all organizations
    """

    serializer_class = OrganizationSerializer

    def get_queryset(self):
        user = self.request.user

        # Superuser sees all organizations
        if user.is_superuser:
            return OrganizationProfile.objects.select_related("tenant")

        # Normal users see ONLY their tenant's organization
        return OrganizationProfile.objects.select_related("tenant").filter(
            tenant=user.tenant
        )

    def get_object(self):
        """
        Defensive object-level tenant isolation.
        """
        obj = super().get_object()
        user = self.request.user

        if not user.is_superuser and obj.tenant != user.tenant:
            raise PermissionDenied("You do not have access to this organization.")

        return obj

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        org = self.get_object()
        OrganizationService.suspend(request.user, org)
        return Response(self.get_serializer(org).data)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        org = self.get_object()
        OrganizationService.activate(request.user, org)
        return Response(self.get_serializer(org).data)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        org = self.get_object()
        OrganizationService.archive(request.user, org)
        return Response(self.get_serializer(org).data)
