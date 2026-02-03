from django.core.management.base import BaseCommand
from core.models import (
    Tenant,
    Role,
    Permission,
    RolePermission,
)

# ─────────────────────────────
# ROLE POLICIES
# ─────────────────────────────
ROLE_POLICIES = {
    "SuperAdmin": lambda perm: True,

    "ModuleAdmin": lambda perm: perm.action.code in {
        "view", "create", "update", "delete", "approve"
    },

    "Editor": lambda perm: perm.action.code in {
        "view", "create", "update"
    },

    "Approver": lambda perm: perm.action.code == "approve",

    "Viewer": lambda perm: perm.action.code == "view",
}


class Command(BaseCommand):
    help = "Seed tenant-scoped roles using policy-based permission assignment"

    def handle(self, *args, **options):
        tenants = Tenant.objects.all()

        if not tenants.exists():
            self.stderr.write("❌ No tenants found. Seed tenants first.")
            return

        for tenant in tenants:
            self.stdout.write(f"\n🔹 Seeding roles for tenant: {tenant.name}")

            permissions = Permission.objects.filter(tenant=tenant)

            if not permissions.exists():
                self.stderr.write(
                    f"⚠ No permissions found for tenant {tenant.name}"
                )
                continue

            for role_name, policy_fn in ROLE_POLICIES.items():
                role, _ = Role.objects.get_or_create(
                    name=role_name,
                    tenant=tenant,
                )

                created = 0

                for perm in permissions:
                    if not policy_fn(perm):
                        continue

                    _, rp_created = RolePermission.objects.get_or_create(
                        role=role,
                        permission=perm,
                        defaults={"allowed": True},
                    )

                    if rp_created:
                        created += 1

                self.stdout.write(
                    f"  ✔ {role.name}: +{created} permissions"
                )

        self.stdout.write(
            self.style.SUCCESS("\n✅ Role seeding completed successfully")
        )
