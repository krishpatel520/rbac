from django.core.management.base import BaseCommand
from core.models import Tenant, TenantModule, Action, Permission

class Command(BaseCommand):
    help = "Seed permissions for all tenant modules and actions"

    def handle(self, *args, **options):
        tenant = Tenant.objects.get(name="TestTenant")
        actions = list(Action.objects.all())

        for tenant_module in TenantModule.objects.filter(tenant=tenant):
            for action in actions:
                Permission.objects.get_or_create(
                    tenant=tenant,
                    tenant_module=tenant_module,
                    action=action,
                )

        self.stdout.write(self.style.SUCCESS("✔ Permissions seeded"))
