from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from followup.models import FollowUp
from followup.services import FollowUpService
from followup.api.serializers import FollowUpSerializer
from enquiry.models import Enquiry


class FollowUpViewSet(viewsets.ViewSet):
    """
    REST-style FollowUp API
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=FollowUpSerializer(many=True))
    def list(self, request):
        qs = FollowUp.objects.filter(tenant=request.user.tenant)
        serializer = FollowUpSerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(responses=FollowUpSerializer)
    def retrieve(self, request, pk=None):
        followup = FollowUp.objects.get(
            pk=pk,
            tenant=request.user.tenant,
        )
        return Response(FollowUpSerializer(followup).data)

    @extend_schema(
        request=FollowUpSerializer,
        responses=FollowUpSerializer,
    )
    def create(self, request):
        serializer = FollowUpSerializer(data=request.data)
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
            FollowUpSerializer(followup).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(responses=FollowUpSerializer)
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        followup = FollowUp.objects.get(
            pk=pk,
            tenant=request.user.tenant,
        )
        followup = FollowUpService.complete(request.user, followup)
        return Response(FollowUpSerializer(followup).data)

    @extend_schema(responses=FollowUpSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        followup = FollowUp.objects.get(
            pk=pk,
            tenant=request.user.tenant,
        )
        followup = FollowUpService.cancel(request.user, followup)
        return Response(FollowUpSerializer(followup).data)
