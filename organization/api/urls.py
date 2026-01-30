from rest_framework.routers import DefaultRouter
from organization.api.views import OrganizationViewSet

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organization")

urlpatterns = router.urls
