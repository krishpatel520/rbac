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
        """
        Determines the current tenant from the user object and sets it in the thread-local context.
        """
        tenant = None

        if request.user.is_authenticated:
            tenant = getattr(request.user, "tenant", None)

        if tenant:
            set_current_tenant(tenant)

    def process_response(self, request, response):
        """
        Clears the tenant from the thread-local context after the request is processed.
        """
        clear_current_tenant()
        return response

