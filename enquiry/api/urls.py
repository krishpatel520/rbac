from rest_framework.routers import DefaultRouter
from enquiry.api.views import EnquiryViewSet


router = DefaultRouter()
router.register(r"enquiries", EnquiryViewSet, basename="enquiry")


urlpatterns = router.urls