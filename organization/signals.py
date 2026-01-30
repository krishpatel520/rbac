from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Tenant
from organization.models import OrganizationProfile, OrganizationStatus


@receiver(post_save, sender=Tenant)
def create_organization_profile(sender, instance, created, **kwargs):
    """
    Ensure every Tenant has exactly one OrganizationProfile.
    """
    if created:
        OrganizationProfile.objects.create(
            tenant=instance,
            status=OrganizationStatus.ACTIVE,
        )
