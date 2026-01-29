from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from followup.models import FollowUp
from followup.services import FollowUpService
from core.decorators import require_permission


# ─────────────────────────────
# READ-ONLY VIEWS
# ─────────────────────────────

@require_permission("followup.view")
@login_required
def followup_list(request):
    """
    List followups for the active tenant.
    Tenant isolation is enforced by TenantAwareManager.
    """
    followups = FollowUp.objects.all()
    return render(
        request,
        "followup/followup_list.html",
        {"followups": followups},
    )


# ─────────────────────────────
# STATE TRANSITION VIEWS
# ─────────────────────────────

@require_permission("followup.complete", model=FollowUp)
@login_required
def complete_followup(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)

    FollowUpService.complete(
        user=request.user,
        followup=followup,
    )

    return redirect("followup_list")


@require_permission("followup.cancel", model=FollowUp)
@login_required
def cancel_followup(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)

    FollowUpService.cancel(
        user=request.user,
        followup=followup,
    )

    return redirect("followup_list")
