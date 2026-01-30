from rest_framework.routers import DefaultRouter
from quotation.api.views import QuotationViewSet

router = DefaultRouter()
router.register(r"quotations", QuotationViewSet, basename="quotation")

urlpatterns = router.urls
