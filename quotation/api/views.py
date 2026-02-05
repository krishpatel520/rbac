from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from core.api.base import RBACViewSet
from quotation.models import Quotation
from quotation.services import QuotationService
from quotation.api.serializers import QuotationSerializer


class QuotationViewSet(RBACViewSet):
    serializer_class = QuotationSerializer
    
    def get_queryset(self):
        """Override to return fresh queryset and apply tenant filtering"""
        base_qs = Quotation.objects.all()
        tenant = self.request.user.tenant
        return base_qs.filter(tenant=tenant)

    @extend_schema(responses=QuotationSerializer(many=True))
    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)


    @extend_schema(responses=QuotationSerializer)
    def retrieve(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        quotation = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(self.get_serializer(quotation).data)

    @extend_schema(
        request=QuotationSerializer,
        responses=QuotationSerializer,
    )
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quotation = QuotationService.create(
            user=request.user,
            enquiry=serializer.validated_data["enquiry"],
            amount=serializer.validated_data["amount"],
        )

        return Response(
            self.get_serializer(quotation).data,
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
