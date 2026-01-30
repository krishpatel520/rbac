from rest_framework import serializers
from organization.models import OrganizationProfile


class OrganizationSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = OrganizationProfile
        fields = [
            "id",
            "tenant_name",
            "status",
        ]
        read_only_fields = fields
