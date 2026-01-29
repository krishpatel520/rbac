from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from enquiry.models import Enquiry
from enquiry.services import EnquiryService
from core.decorators import require_permission


# ─────────────────────────────
# READ-ONLY VIEWS
# ─────────────────────────────

@require_permission("enquiry.view")
@login_required
def enquiry_list(request):
    """
    List enquiries for the active tenant.
    Tenant isolation is enforced by TenantAwareManager.
    """
    enquiries = Enquiry.objects.all()
    return render(
        request,
        "enquiry/enquiry_list.html",
        {"enquiries": enquiries},
    )


# ─────────────────────────────
# STATE TRANSITION VIEWS
# ─────────────────────────────

@require_permission("enquiry.qualify", model=Enquiry)
@login_required
def qualify_enquiry(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk)

    EnquiryService.qualify(
        user=request.user,
        enquiry=enquiry,
    )

    return redirect("enquiry_list")


@require_permission("enquiry.disqualify", model=Enquiry)
@login_required
def disqualify_enquiry(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk)

    EnquiryService.disqualify(
        user=request.user,
        enquiry=enquiry,
    )

    return redirect("enquiry_list")


@require_permission("enquiry.close", model=Enquiry)
@login_required
def close_enquiry(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk)

    EnquiryService.close(
        user=request.user,
        enquiry=enquiry,
    )

    return redirect("enquiry_list")
