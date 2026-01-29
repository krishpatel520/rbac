from django.shortcuts import get_object_or_404, redirect, render

from quotation.models import Quotation, QuotationStatus
from core.decorators import require_permission


@require_permission("quotation.view")
def quotation_list(request):
    quotations = Quotation.objects.all()
    return render(request, "quotation/quotation_list.html", {"quotations": quotations})


@require_permission("quotation.send", model=Quotation)
def send_quotation(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    quotation.status = QuotationStatus.SENT
    quotation.save()
    return redirect("quotation_list")


@require_permission("quotation.accept", model=Quotation)
def accept_quotation(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    quotation.status = QuotationStatus.ACCEPTED
    quotation.save()
    return redirect("quotation_list")


@require_permission("quotation.reject", model=Quotation)
def reject_quotation(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    quotation.status = QuotationStatus.REJECTED
    quotation.save()
    return redirect("quotation_list")
