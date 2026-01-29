from django.shortcuts import get_object_or_404, redirect, render

from organization.models import OrganizationProfile, OrganizationStatus
from core.decorators import require_permission


@require_permission("organization.view")
def organization_list(request):
    orgs = OrganizationProfile.objects.all()
    return render(request, "organization/org_list.html", {"orgs": orgs})


@require_permission("organization.suspend", model=OrganizationProfile)
def suspend_org(request, pk):
    org = get_object_or_404(OrganizationProfile, pk=pk)
    org.status = OrganizationStatus.SUSPENDED
    org.save()
    return redirect("organization_list")


@require_permission("organization.activate", model=OrganizationProfile)
def activate_org(request, pk):
    org = get_object_or_404(OrganizationProfile, pk=pk)
    org.status = OrganizationStatus.ACTIVE
    org.save()
    return redirect("organization_list")
