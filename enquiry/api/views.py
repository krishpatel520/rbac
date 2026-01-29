from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from django.views.decorators.csrf import csrf_exempt

from enquiry.models import Enquiry
from enquiry.services import EnquiryService
from enquiry.api.serializers import EnquirySerializer


class EnquiryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=EnquirySerializer(many=True))
    def list(self, request):
        qs = Enquiry.objects.filter(tenant=request.user.tenant)
        serializer = EnquirySerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(responses=EnquirySerializer)
    def retrieve(self, request, pk=None):
        enquiry = Enquiry.objects.get(
            pk=pk,
            tenant=request.user.tenant,
        )
        return Response(EnquirySerializer(enquiry).data)

    @extend_schema(
        request=EnquirySerializer,
        responses=EnquirySerializer,
    )
    @csrf_exempt
    def create(self, request):
        serializer = EnquirySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        enquiry = EnquiryService.create_enquiry(
            user=request.user,
            **serializer.validated_data,
        )

        return Response(
            EnquirySerializer(enquiry).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(responses=EnquirySerializer)
    @action(detail=True, methods=["post"])
    def qualify(self, request, pk=None):
        enquiry = Enquiry.objects.get(
            pk=pk,
            tenant=request.user.tenant,
        )
        enquiry = EnquiryService.qualify(request.user, enquiry)
        return Response(EnquirySerializer(enquiry).data)

    @extend_schema(responses=EnquirySerializer)
    @action(detail=True, methods=["post"])
    def disqualify(self, request, pk=None):
        enquiry = Enquiry.objects.get(
            pk=pk,
            tenant=request.user.tenant,
        )
        enquiry = EnquiryService.disqualify(request.user, enquiry)
        return Response(EnquirySerializer(enquiry).data)

    @extend_schema(responses=EnquirySerializer)
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        enquiry = Enquiry.objects.get(
            pk=pk,
            tenant=request.user.tenant,
        )
        enquiry = EnquiryService.close(request.user, enquiry)
        return Response(EnquirySerializer(enquiry).data)
