from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from core.utils import is_allowed


def require_permission(permission_code, model=None, lookup_kwarg="pk"):
    """
    Authorization decorator.

    Parameters:
    - permission_code: str (e.g. 'quotation.accept')
    - model: Django model class (optional)
    - lookup_kwarg: URL kwarg used to fetch the object (default 'pk')

    If model is provided, the object is fetched and passed to ABAC rules.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            obj = None

            # Fetch object if model is provided
            if model is not None:
                obj_id = kwargs.get(lookup_kwarg)
                if obj_id is None:
                    return HttpResponseForbidden("Object identifier missing.")

                obj = get_object_or_404(model, pk=obj_id)

            # Final authorization decision
            if not is_allowed(user, permission_code, obj):
                return HttpResponseForbidden("You are not authorized to perform this action.")

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
