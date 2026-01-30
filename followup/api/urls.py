from rest_framework.routers import DefaultRouter
from followup.api.views import FollowUpViewSet

router = DefaultRouter()
router.register(r"followups", FollowUpViewSet, basename="followup")

urlpatterns = router.urls
