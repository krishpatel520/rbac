"""
Default settings for Django RBAC Core package.

To customize these settings, add them to your Django project's settings.py file.
"""
from django.conf import settings

def get_rbac_tenant_model():
    """
    Return the Tenant model that is active in this project.
    """
    return getattr(settings, 'RBAC_TENANT_MODEL', 'core.Tenant')

# Note: User model is configured via Django's AUTH_USER_MODEL setting
# AUTH_USER_MODEL = 'accounts.User'  # or your custom user model

