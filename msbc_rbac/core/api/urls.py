from msbc_rbac.core.api.views import router, role_permissions
from django.urls import path

urlpatterns = router.urls + [
    path('roles/<int:role_id>/permissions/', role_permissions, name='role-permissions'),
]
