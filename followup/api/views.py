from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from core.api.base import RBACViewSet
from followup.models import FollowUp
from followup.services import FollowUpService
from followup.api.serializers import FollowUpSerializer
from enquiry.models import Enquiry


class FollowUpViewSet(RBACViewSet):
    serializer_class = FollowUpSerializer
    
    def get_queryset(self):
        """Override to return fresh queryset and apply tenant filtering"""
        base_qs = FollowUp.objects.all()
        tenant = self.request.user.tenant
        return base_qs.filter(tenant=tenant)

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        followup = self.get_queryset().get(pk=pk)
        return Response(self.get_serializer(followup).data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        enquiry = Enquiry.objects.get(
            pk=serializer.validated_data["enquiry"].id,
            tenant=request.user.tenant,
        )

        followup = FollowUpService.create_followup(
            user=request.user,
            enquiry=enquiry,
            note=serializer.validated_data.get("note", ""),
        )

        return Response(
            self.get_serializer(followup).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        followup = self.get_queryset().get(pk=pk)
        followup = FollowUpService.complete(request.user, followup)
        return Response(self.get_serializer(followup).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        followup = self.get_queryset().get(pk=pk)
        followup = FollowUpService.cancel(request.user, followup)
        return Response(self.get_serializer(followup).data)
