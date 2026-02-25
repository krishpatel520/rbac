"""
Catch-all JSON exception middleware.

Converts all unhandled exceptions into structured JSON responses.
``RBACPermissionDenied`` from the RBAC middleware is intercepted here
and returned as a descriptive 403 with the exact rule that was violated.
"""
import logging
import traceback

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, JsonResponse

from core.exceptions import RBACPermissionDenied

logger = logging.getLogger(__name__)


class JSONExceptionMiddleware:
    """
    Middleware to catch all exceptions and return structured JSON responses.

    Order of priority:
      1. RBACPermissionDenied  → 403  with violation detail
      2. Django PermissionDenied → 403
      3. Http404               → 404
      4. ValidationError       → 400
      5. Anything else         → 500  (traceback included in DEBUG mode)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Convert exceptions to JSON responses."""

        logger.error(
            "Exception on %s %s: %s",
            request.method,
            request.path,
            str(exception),
            exc_info=True,
        )

        # ── 1. RBAC-specific access violation ──────────────────────────
        if isinstance(exception, RBACPermissionDenied):
            return JsonResponse(
                {
                    "error": "Unauthorized Access",
                    "violation": exception.violation_type,
                    "detail": exception.detail,
                    "status_code": 403,
                    "path": request.path,
                },
                status=403,
            )

        # ── 2. Generic Django permission denial ────────────────────────
        if isinstance(exception, PermissionDenied):
            return JsonResponse(
                {
                    "error": "Forbidden",
                    "status_code": 403,
                    "detail": str(exception) or "You do not have permission to access this resource.",
                    "path": request.path,
                },
                status=403,
            )

        # ── 3. Not found ───────────────────────────────────────────────
        if isinstance(exception, Http404):
            return JsonResponse(
                {
                    "error": "Not Found",
                    "status_code": 404,
                    "detail": str(exception) or "The requested resource was not found.",
                    "path": request.path,
                },
                status=404,
            )

        # ── 4. Validation error ────────────────────────────────────────
        if isinstance(exception, ValidationError):
            return JsonResponse(
                {
                    "error": "Validation Error",
                    "status_code": 400,
                    "detail": str(exception),
                    "path": request.path,
                },
                status=400,
            )

        # ── 5. Unexpected server error ─────────────────────────────────
        error_data = {
            "error": "Internal Server Error",
            "status_code": 500,
            "detail": "An unexpected error occurred. Please contact support.",
            "path": request.path,
        }

        if settings.DEBUG:
            error_data["debug"] = {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc(),
            }

        return JsonResponse(error_data, status=500)
