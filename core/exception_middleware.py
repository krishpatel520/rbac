"""
Middleware to catch all exceptions and return JSON responses.
"""
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
import logging
import traceback
from django.conf import settings

logger = logging.getLogger(__name__)


class JSONExceptionMiddleware:
    """
    Middleware to catch all exceptions and return JSON responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Convert exceptions to JSON responses.
        """
        
        # Log the exception
        logger.error(
            f"Exception on {request.method} {request.path}: {str(exception)}",
            exc_info=True
        )

        # Handle specific exception types
        if isinstance(exception, Http404):
            return JsonResponse({
                'error': 'Not Found',
                'status_code': 404,
                'message': str(exception) or 'The requested resource was not found.',
                'path': request.path
            }, status=404)

        elif isinstance(exception, PermissionDenied):
            return JsonResponse({
                'error': 'Forbidden',
                'status_code': 403,
                'message': str(exception) or 'You do not have permission to access this resource.',
                'path': request.path
            }, status=403)

        elif isinstance(exception, ValidationError):
            return JsonResponse({
                'error': 'Validation Error',
                'status_code': 400,
                'message': str(exception),
                'path': request.path
            }, status=400)

        # Handle all other exceptions as 500
        error_data = {
            'error': 'Internal Server Error',
            'status_code': 500,
            'message': 'An unexpected error occurred.',
            'path': request.path
        }

        # Include detailed error info in DEBUG mode
        if settings.DEBUG:
            error_data['debug'] = {
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            }

        return JsonResponse(error_data, status=500)
