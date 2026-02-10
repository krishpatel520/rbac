"""
Custom exception handler for Django REST Framework.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.http import Http404
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that ensures consistent JSON error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the response data structure
        custom_response_data = {
            'error': response.status_text if hasattr(response, 'status_text') else 'Error',
            'status_code': response.status_code,
            'message': response.data.get('detail', str(exc)) if isinstance(response.data, dict) else str(response.data),
        }
        
        # Add any additional error details
        if isinstance(response.data, dict):
            for key, value in response.data.items():
                if key != 'detail':
                    custom_response_data[key] = value
        
        # Add request path if available
        request = context.get('request')
        if request:
            custom_response_data['path'] = request.path
        
        response.data = custom_response_data
    else:
        # Handle exceptions not handled by DRF
        if isinstance(exc, Http404):
            response = Response({
                'error': 'Not Found',
                'status_code': 404,
                'message': str(exc) or 'The requested resource was not found.',
                'path': context.get('request').path if context.get('request') else None
            }, status=404)
        elif isinstance(exc, PermissionDenied):
            response = Response({
                'error': 'Forbidden',
                'status_code': 403,
                'message': str(exc) or 'You do not have permission to access this resource.',
                'path': context.get('request').path if context.get('request') else None
            }, status=403)

    return response
