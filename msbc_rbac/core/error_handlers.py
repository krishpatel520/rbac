"""
Custom error handlers for JSON responses.
"""
from django.http import JsonResponse
from django.views.defaults import page_not_found, server_error, bad_request, permission_denied
import logging

logger = logging.getLogger(__name__)


def json_404_handler(request, exception=None):
    """
    Custom 404 handler that returns JSON response.
    """
    return JsonResponse({
        'error': 'Not Found',
        'status_code': 404,
        'message': 'The requested resource was not found.',
        'path': request.path
    }, status=404)


def json_500_handler(request):
    """
    Custom 500 handler that returns JSON response.
    """
    logger.error(f"Internal server error on path: {request.path}")
    return JsonResponse({
        'error': 'Internal Server Error',
        'status_code': 500,
        'message': 'An unexpected error occurred. Please try again later.',
        'path': request.path
    }, status=500)


def json_400_handler(request, exception=None):
    """
    Custom 400 handler that returns JSON response.
    """
    return JsonResponse({
        'error': 'Bad Request',
        'status_code': 400,
        'message': 'The request could not be understood by the server.',
        'path': request.path
    }, status=400)


def json_403_handler(request, exception=None):
    """
    Custom 403 handler that returns JSON response.
    """
    return JsonResponse({
        'error': 'Forbidden',
        'status_code': 403,
        'message': 'You do not have permission to access this resource.',
        'path': request.path
    }, status=403)
