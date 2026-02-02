from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver

from rest_framework.views import APIView

from core.models import (
    ApiEndpoint,
    ApiOperation,
    Action,
    Module,
    SubModule,
)

class Command(BaseCommand):
    help = "Universal API registry sync (ViewSet, APIView, CBV, FBV, Router-safe)"

    HTTP_ACTION_MAP = {
        "get": "read",
        "post": "create",
        "put": "update",
        "patch": "partial_update",
        "delete": "delete",
    }

    # -------------------------
    # Entry Point
    # -------------------------
    def handle(self, *args, **options):
        resolver = get_resolver()
        default_module = self._get_default_module()
        print("default module >>>",default_module)

        urlpatterns = []
        self._collect_urlpatterns(
            resolver.url_patterns,
            urlpatterns=urlpatterns,
            prefix=""
        )

        created_endpoints = 0
        created_operations = 0

        for raw_path, callback in urlpatterns:
            path = self._normalize_path(raw_path)
            print("path >>>>",path)

            endpoint, ep_created = ApiEndpoint.objects.get_or_create(
                path=path,
                module=default_module,
            )
            print(endpoint, "endpoint")
            if ep_created:
                created_endpoints += 1

            actions = self._resolve_actions(callback)

            for raw_action in actions:
                action_code = self._normalize_action(raw_action)
                action = self._get_or_create_action(action_code)

                _, op_created = ApiOperation.objects.get_or_create(
                    endpoint=endpoint,
                    action=action,
                    defaults={
                        "is_enabled": True,
                    },
                )

                if op_created:
                    created_operations += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"API sync completed | "
                f"Endpoints +{created_endpoints} | "
                f"Operations +{created_operations}"
            )
        )

    # -------------------------
    # URL Collection
    # -------------------------
    def _collect_urlpatterns(self, patterns, urlpatterns, prefix):
        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                urlpatterns.append(
                    (prefix + str(pattern.pattern), pattern.callback)
                )
            elif isinstance(pattern, URLResolver):
                self._collect_urlpatterns(
                    pattern.url_patterns,
                    urlpatterns,
                    prefix + str(pattern.pattern)
                )

    # -------------------------
    # Path Helpers
    # -------------------------
    def _normalize_path(self, raw_path):
        return "/" + raw_path.lstrip("/")

    # -------------------------
    # Action Resolution
    # -------------------------
    def _resolve_actions(self, callback):
        """
        Detect actions for all view types:
        - ViewSet / ModelViewSet
        - APIView / GenericAPIView
        - Django CBV
        - Function-based views
        """
        actions = set()

        # DRF ViewSet (router based)
        if hasattr(callback, "actions"):
            actions.update(callback.actions.values())
            return actions

        view_cls = getattr(callback, "cls", None)

        # DRF APIView / GenericAPIView
        if view_cls and issubclass(view_cls, APIView):
            for method in view_cls.http_method_names:
                if hasattr(view_cls, method):
                    actions.add(method)
            return actions

        # Django Class-Based View
        if view_cls:
            for method in ("get", "post", "put", "patch", "delete"):
                if hasattr(view_cls, method):
                    actions.add(method)
            return actions

        # Function-Based View
        if callable(callback):
            actions.add("get")  # safe fallback
            return actions

        return actions

    # -------------------------
    # Action Helpers
    # -------------------------
    def _normalize_action(self, raw_action):
        return self.HTTP_ACTION_MAP.get(raw_action, raw_action)

    def _get_or_create_action(self, action_code):
        action, _ = Action.objects.get_or_create(code=action_code)
        return action

    # -------------------------
    # Defaults
    # -------------------------
    def _get_default_module(self):
        module, _ = Module.objects.get_or_create(
            name="Uncategorized"
        )
        print("Module >>>", module)
        return module
