"""
Custom exception handler for Django REST Framework.

Ensures consistent JSON error responses for all DRF views.
``RBACPermissionDenied`` is handled here so that API views also receive
accurate 403 responses with the exact RBAC rule that was violated.
"""
import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.exceptions import RBACPermissionDenied

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler that returns consistent JSON error responses.

    Resolution order:
      1. RBACPermissionDenied  → 403  with full violation detail
      2. Standard DRF handling → wraps into our envelope
      3. Http404 / PermissionDenied not handled by DRF → 404 / 403
    """
    request = context.get("request")
    path = request.path if request else None

    # ── 1. RBAC-specific access violation ──────────────────────────────
    if isinstance(exc, RBACPermissionDenied):
        logger.warning(
            "RBAC denied [%s] %s %s — %s",
            exc.violation_type,
            request.method if request else "?",
            path,
            exc.detail,
        )
        return Response(
            {
                "error": "Unauthorized Access",
                "violation": exc.violation_type,
                "detail": exc.detail,
                "status_code": 403,
                "path": path,
            },
            status=403,
        )

    # ── 2. Let DRF handle its own exceptions first ──────────────────────
    response = exception_handler(exc, context)

    if response is not None:
        # Wrap DRF response into our standard envelope
        custom_data = {
            "error": getattr(response, "status_text", "Error"),
            "status_code": response.status_code,
            "detail": (
                response.data.get("detail", str(exc))
                if isinstance(response.data, dict)
                else str(response.data)
            ),
            "path": path,
        }
        # Preserve any extra DRF fields (e.g. field-level validation errors)
        if isinstance(response.data, dict):
            for key, value in response.data.items():
                if key not in ("detail",):
                    custom_data[key] = value
        response.data = custom_data
        return response

    # ── 3. Exceptions DRF does not handle natively ──────────────────────
    if isinstance(exc, Http404):
        return Response(
            {
                "error": "Not Found",
                "status_code": 404,
                "detail": str(exc) or "The requested resource was not found.",
                "path": path,
            },
            status=404,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {
                "error": "Forbidden",
                "status_code": 403,
                "detail": str(exc) or "You do not have permission to access this resource.",
                "path": path,
            },
            status=403,
        )

    return None
