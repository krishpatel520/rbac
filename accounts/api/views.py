"""
API views for accounts app - Token authentication endpoint.
"""
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, OpenApiResponse


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'example': 'editor_a'},
                'password': {'type': 'string', 'example': 'editor_a'},
            },
            'required': ['username', 'password']
        }
    },
    responses={
        200: OpenApiResponse(
            description='Token generated successfully',
            response={
                'type': 'object',
                'properties': {
                    'token': {'type': 'string', 'example': '9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b'},
                    'user_id': {'type': 'integer', 'example': 1},
                    'username': {'type': 'string', 'example': 'editor_a'},
                    'tenant': {'type': 'string', 'example': 'Tenant A'},
                }
            }
        ),
        400: OpenApiResponse(description='Invalid credentials'),
    },
    tags=['Authentication'],
    summary='Obtain API Token',
    description="""
    Generate or retrieve an API authentication token for a user.
    
    **Usage:**
    1. POST your username and password to this endpoint
    2. Receive a token in the response
    3. Use the token in subsequent API requests by adding the header:
       `Authorization: Token <your-token-here>`
    
    **Token Lifetime:**
    - Tokens do not expire automatically
    - One token per user (regenerate by calling this endpoint again)
    - To revoke access, delete the token from the admin panel
    
    **Example:**
    ```bash
    curl -X POST http://127.0.0.1:8000/api/auth/token/ \\
      -H "Content-Type: application/json" \\
      -d '{"username": "editor_a", "password": "editor_a"}'
    ```
    """
)
@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_auth_token(request):
    """
    Generate or retrieve API token for user authentication.
    
    This endpoint allows users to obtain an authentication token by providing
    their username and password. The token can then be used for API requests.
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Both username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user:
        # Get or create token for this user
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'tenant': user.tenant.name,
        }, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_400_BAD_REQUEST
        )
