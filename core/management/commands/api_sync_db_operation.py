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
    help = "Sync application API endpoints and operations into RBAC tables"

    HTTP_ACTION_MAP = {
        "get": "view",
        "post": "create",
        "put": "update",
        "patch": "update",
        "delete": "delete",
    }

    # 🚫 Never register these in RBAC
    SKIP_PATH_PREFIXES = (
        "/admin/",
        "/static/",
        "/media/",
        "/accounts/",
        "/api/schema",
    )

    def handle(self, *args, **options):
        resolver = get_resolver()
        default_module = self._get_default_module()

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

            if self._should_skip_path(path):
                continue

            endpoint, ep_created = ApiEndpoint.objects.get_or_create(
                path=path,
                defaults={"module": default_module},
            )
            if ep_created:
                created_endpoints += 1

            http_methods = self._resolve_http_methods(callback)

            for method in http_methods:
                action_code = self.HTTP_ACTION_MAP.get(method, method)
                action, _ = Action.objects.get_or_create(code=action_code)

                _, op_created = ApiOperation.objects.get_or_create(
                    endpoint=endpoint,
                    http_method=method.upper(),
                    defaults={
                        "action": action,
                        "is_enabled": True,
                    },
                )

                if op_created:
                    created_operations += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✔ API sync completed | "
                f"Endpoints +{created_endpoints} | "
                f"Operations +{created_operations}"
            )
        )

    # ─────────────────────────────
    # URL Collection
    # ─────────────────────────────
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

    # ─────────────────────────────
    # Helpers
    # ─────────────────────────────
    def _normalize_path(self, raw_path):
        return "/" + raw_path.lstrip("/")

    def _should_skip_path(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.SKIP_PATH_PREFIXES)

    def _resolve_http_methods(self, callback):
        methods = set()

        # DRF ViewSet
        if hasattr(callback, "actions"):
            return {m.lower() for m in callback.actions.keys()}

        view_cls = getattr(callback, "cls", None)

        # DRF APIView / GenericAPIView
        if view_cls and issubclass(view_cls, APIView):
            for method in view_cls.http_method_names:
                if hasattr(view_cls, method):
                    methods.add(method)
            return methods

        # Django CBV
        if view_cls:
            for method in ("get", "post", "put", "patch", "delete"):
                if hasattr(view_cls, method):
                    methods.add(method)
            return methods

        # FBV fallback
        return {"get"}

    def _get_default_module(self):
        module, _ = Module.objects.get_or_create(
            code="SYSTEM",
            defaults={"name": "System"},
        )
        return module
