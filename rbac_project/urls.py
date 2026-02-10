"""
URL configuration for rbac_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from accounts.api.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core(dashboard + RBAC protected views)
    path('', include('core.urls')),

    # Authentication
    path('accounts/', include('accounts.urls')),
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),  # Token authentication

    # OpenAPI schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),

    # Core / Demo API
    path('api/core/', include('core.api.urls')),

    # Enquiry API - Commented out as they don't exist yet
    # path('api/', include('enquiry.api.urls')),

    # FollowUp API
    # path('api/', include('followup.api.urls')),

    # Organization API
    # path('api/', include('organization.api.urls')),

    # Quotation API
    # path('api/', include('quotation.api.urls')),
]

# ------------------------------------------------------------------------------
# Custom Error Handlers (JSON responses)
# ------------------------------------------------------------------------------
from core.error_handlers import (
    json_404_handler,
    json_500_handler,
    json_400_handler,
    json_403_handler,
)

handler404 = json_404_handler
handler500 = json_500_handler
handler400 = json_400_handler
handler403 = json_403_handler

