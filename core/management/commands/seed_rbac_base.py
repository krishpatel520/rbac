from django.core.management.base import BaseCommand
from core.models import (
    Tenant,
    Module,
    SubModule,
    Action,
    ModuleSubModuleMapping,
    TenantModule,
)

class Command(BaseCommand):
    help = "Seed base RBAC entities (tenant, modules, submodules, actions)"

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.get_or_create(
            name="TestTenant",
            defaults={"is_active": True},
        )

        modules = {
            "CRM": ["LEADS", "DEALS"],
            "OPS": ["TASKS", "REPORTS"],
        }

        actions = ["view", "create", "update", "delete", "approve"]

        for action_code in actions:
            Action.objects.get_or_create(code=action_code)

        for module_code, submodules in modules.items():
            module, _ = Module.objects.get_or_create(
                code=module_code,
                defaults={"name": module_code.title()},
            )

            for sub_code in submodules:
                submodule, _ = SubModule.objects.get_or_create(
                    code=sub_code,
                    defaults={"name": sub_code.title()},
                )

                ModuleSubModuleMapping.objects.get_or_create(
                    module=module,
                    submodule=submodule,
                )

                TenantModule.objects.get_or_create(
                    tenant=tenant,
                    module=module,
                    submodule=submodule,
                    defaults={"is_enabled": True},
                )

        self.stdout.write(self.style.SUCCESS("✔ Base RBAC entities seeded"))
