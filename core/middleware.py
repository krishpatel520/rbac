from django.utils.deprecation import MiddlewareMixin
from django.apps import apps
from django.conf import settings

from core.tenant_context import (
    set_current_tenant,
    clear_current_tenant,
)


class CurrentTenantMiddleware(MiddlewareMixin):
    """
    Resolves tenant for the request and stores it in thread-local storage.
    """

    def process_request(self, request):
        tenant = None

        if request.user.is_authenticated:
            tenant = getattr(request.user, "tenant", None)

        if tenant:
            set_current_tenant(tenant)

    def process_response(self, request, response):
        clear_current_tenant()
        return response

