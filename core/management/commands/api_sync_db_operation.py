from django.core.management.base import BaseCommand
from django.apps import apps
from django.urls import get_resolver, URLPattern, URLResolver
from rest_framework.views import APIView

from core.models import ApiEndpoint, ApiOperation, Module, SubModule


class Command(BaseCommand):
    """
    Auto sync APIs + Module/SubModule from Django apps.py metadata.
    """

    help = "Auto sync APIs + module/submodule from apps.py"

    HTTP_ACTION_MAP = {
        "get": "view",
        "post": "create",
        "put": "update",
        "patch": "update",
        "delete": "delete",
    }

    SKIP_PATH_PREFIXES = (
        "/admin/",
        "/static/",
        "/media/",
        "/accounts/",
        "/api/schema",
        "/api/docs",
    )

    def handle(self, *args, **options):
        resolver = get_resolver()
        urlpatterns = []
        self._collect_urlpatterns(resolver.url_patterns, urlpatterns, "")

        system_module = self._get_or_create_module("SYSTEM", "System")
        system_submodule = None

        created_endpoints = 0
        created_operations = 0
        updated_module_map = 0

        for raw_path, callback in urlpatterns:
            path = self._normalize_path(raw_path)

            if self._should_skip_path(path):
                continue

            # Detect module/submodule from app config
            module_obj, submodule_obj = self._resolve_module_from_callback(callback)

            if not module_obj:
                module_obj = system_module
                submodule_obj = system_submodule

            # Create endpoint
            endpoint, ep_created = ApiEndpoint.objects.get_or_create(
                path=path,
                defaults={
                    "module": module_obj,
                    "submodule": submodule_obj,
                },
            )

            # Update module mapping if changed
            if not ep_created and (
                endpoint.module != module_obj or endpoint.submodule != submodule_obj
            ):
                endpoint.module = module_obj
                endpoint.submodule = submodule_obj
                endpoint.save(update_fields=["module", "submodule"])
                updated_module_map += 1

            if ep_created:
                created_endpoints += 1

            # Resolve HTTP methods
            methods = self._resolve_http_methods(callback)

            for method in methods:
                permission_code = self.HTTP_ACTION_MAP.get(method, method)

                _, created = ApiOperation.objects.get_or_create(
                    endpoint=endpoint,
                    http_method=method.upper(),
                    defaults={
                        "permission_code": permission_code,
                        "is_enabled": True,
                    },
                )

                if created:
                    created_operations += 1

        self.stdout.write(self.style.SUCCESS(
            f"✔ API Sync Completed\n"
            f"Endpoints created: {created_endpoints}\n"
            f"Operations created: {created_operations}\n"
            f"Module mappings updated: {updated_module_map}"
        ))

    # ─────────────────────────────
    # URL Collector
    # ─────────────────────────────
    def _collect_urlpatterns(self, patterns, urlpatterns, prefix):
        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                urlpatterns.append((prefix + str(pattern.pattern), pattern.callback))
            elif isinstance(pattern, URLResolver):
                self._collect_urlpatterns(
                    pattern.url_patterns, urlpatterns, prefix + str(pattern.pattern)
                )

    # ─────────────────────────────
    # Module Resolver from apps.py
    # ─────────────────────────────
    def _resolve_module_from_callback(self, callback):
        """
        Detect Django app from callback and read RBAC_MODULE / RBAC_SUBMODULE
        """
        view_cls = getattr(callback, "cls", None)
        module_path = None

        if view_cls:
            module_path = view_cls.__module__
        else:
            module_path = callback.__module__

        app_config = apps.get_containing_app_config(module_path)

        if not app_config:
            return None, None

        # Default: submodule = app label
        submodule_code = getattr(app_config, "RBAC_SUBMODULE", app_config.label.upper())
        module_code = getattr(app_config, "RBAC_MODULE", None)

        if not module_code:
            return None, None

        module_obj = self._get_or_create_module(module_code, module_code.title())
        submodule_obj = self._get_or_create_submodule(submodule_code, submodule_code.title())

        return module_obj, submodule_obj

    # ─────────────────────────────
    # Helpers
    # ─────────────────────────────

    def _normalize_path(self, raw_path):
        path = "/" + raw_path.lstrip("/")
        return path.replace("<int:", "{").replace("<str:", "{").replace(">", "}")

    def _should_skip_path(self, path):
        return any(path.startswith(p) for p in self.SKIP_PATH_PREFIXES)

    def _resolve_http_methods(self, callback):
        methods = set()

        if hasattr(callback, "actions"):
            return {m.lower() for m in callback.actions.keys()}

        view_cls = getattr(callback, "cls", None)

        if view_cls and issubclass(view_cls, APIView):
            return {m for m in view_cls.http_method_names if hasattr(view_cls, m)}

        if view_cls:
            return {m for m in ["get", "post", "put", "patch", "delete"] if hasattr(view_cls, m)}

        return {"get"}

    def _get_or_create_module(self, code, name):
        return Module.objects.get_or_create(code=code, defaults={"name": name})[0]

    def _get_or_create_submodule(self, code, name):
        return SubModule.objects.get_or_create(code=code, defaults={"name": name})[0]
