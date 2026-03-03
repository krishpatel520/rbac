from core.tenant_context import set_current_tenant, clear_current_tenant

class TenantContextMiddleware:
    """
    Middleware to ensure the current tenant is set in thread-local storage
    for TenantAwareManager to work correctly.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user and request.user.is_authenticated:
            tenant = getattr(request.user, "tenant", None)
            if tenant:
                set_current_tenant(tenant)

        try:
            response = self.get_response(request)
            return response
        finally:
            clear_current_tenant()
