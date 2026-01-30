from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from quotation.models import Quotation
from quotation.services import QuotationService
from quotation.api.serializers import QuotationSerializer


class QuotationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=QuotationSerializer(many=True))
    def list(self, request):
        qs = Quotation.objects.filter(tenant=request.user.tenant)
        return Response(QuotationSerializer(qs, many=True).data)

    @extend_schema(responses=QuotationSerializer)
    def retrieve(self, request, pk=None):
        quotation = Quotation.objects.get(
            pk=pk,
            tenant=request.user.tenant,
        )
        return Response(QuotationSerializer(quotation).data)

    @extend_schema(
        request=QuotationSerializer,
        responses=QuotationSerializer,
    )
    def create(self, request):
        serializer = QuotationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quotation = QuotationService.create(
            user=request.user,
            enquiry=serializer.validated_data["enquiry"],
            amount=serializer.validated_data["amount"],
        )

        return Response(
            QuotationSerializer(quotation).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(responses=QuotationSerializer)
    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        quotation = Quotation.objects.get(pk=pk, tenant=request.user.tenant)
        quotation = QuotationService.send(request.user, quotation)
        return Response(QuotationSerializer(quotation).data)

    @extend_schema(responses=QuotationSerializer)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        quotation = Quotation.objects.get(pk=pk, tenant=request.user.tenant)
        quotation = QuotationService.accept(request.user, quotation)
        return Response(QuotationSerializer(quotation).data)

    @extend_schema(responses=QuotationSerializer)
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        quotation = Quotation.objects.get(pk=pk, tenant=request.user.tenant)
        quotation = QuotationService.reject(request.user, quotation)
        return Response(QuotationSerializer(quotation).data)

    @extend_schema(responses=QuotationSerializer)
    @action(detail=True, methods=["post"])
    def expire(self, request, pk=None):
        quotation = Quotation.objects.get(pk=pk, tenant=request.user.tenant)
        quotation = QuotationService.expire(request.user, quotation)
        return Response(QuotationSerializer(quotation).data)
