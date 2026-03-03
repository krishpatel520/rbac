"""
Custom exceptions for the RBAC system.

These give the middleware and exception handlers precise, structured
error information so that every access violation is surfaced to the
caller as a clear JSON 403 response rather than a generic 500.
"""


class RBACPermissionDenied(Exception):
    """
    Raised by RBACMiddleware whenever a request is blocked.

    Attributes
    ----------
    violation_type : str
        A short machine-readable key describing which rule was violated.
        Callers can use this for logging, alerting, or client-side branching.
    detail : str
        A human-readable sentence explaining exactly what was violated.
    """

    # ----------------------------------------------------------------
    # Violation type constants — use these everywhere instead of raw strings
    # so that consumers can do  e.g.  `except RBACPermissionDenied as e: if e.violation_type == RBACPermissionDenied.API_NOT_REGISTERED:`
    # ----------------------------------------------------------------
    API_NOT_REGISTERED      = "api_not_registered"
    API_DISABLED_GLOBALLY   = "api_disabled_globally"
    TENANT_NOT_SUBSCRIBED   = "tenant_not_subscribed"
    MODULE_DISABLED         = "module_disabled_for_tenant"
    SUBSCRIPTION_EXPIRED    = "tenant_subscription_expired"
    API_DISABLED_FOR_TENANT = "api_disabled_for_tenant"
    API_BLOCKED_FOR_USER    = "api_blocked_for_user"
    UNKNOWN_ACTION          = "unknown_action_mapping"
    PERMISSION_DENIED       = "permission_denied"

    def __init__(self, violation_type: str, detail: str):
        self.violation_type = violation_type
        self.detail = detail
        super().__init__(detail)

    def __str__(self):
        return f"[{self.violation_type}] {self.detail}"
