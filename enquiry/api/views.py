from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from core.api.base import RBACViewSet
from enquiry.models import Enquiry
from enquiry.services import EnquiryService
from enquiry.api.serializers import EnquirySerializer


class EnquiryViewSet(RBACViewSet):
    serializer_class = EnquirySerializer
    
    def get_queryset(self):
        """Override to return fresh queryset and apply tenant filtering"""
        # Get base queryset (fresh, not cached)
        base_qs = Enquiry.objects.all()
        
        # Apply tenant filtering from RBACViewSet
        tenant = self.request.user.tenant
        return base_qs.filter(tenant=tenant)

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        enquiry = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(self.get_serializer(enquiry).data)



    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        enquiry = EnquiryService.create_enquiry(
            user=request.user,
            **serializer.validated_data,
        )

        return Response(
            self.get_serializer(enquiry).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def qualify(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        enquiry = get_object_or_404(self.get_queryset(), pk=pk)
        enquiry = EnquiryService.qualify(request.user, enquiry)
        return Response(self.get_serializer(enquiry).data)

    @action(detail=True, methods=["post"])
    def disqualify(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        enquiry = get_object_or_404(self.get_queryset(), pk=pk)
        enquiry = EnquiryService.disqualify(request.user, enquiry)
        return Response(self.get_serializer(enquiry).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        enquiry = get_object_or_404(self.get_queryset(), pk=pk)
        enquiry = EnquiryService.close(request.user, enquiry)
        return Response(self.get_serializer(enquiry).data)
