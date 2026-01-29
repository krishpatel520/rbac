from django.core.management.base import BaseCommand
from core.models import Role, Permission, RolePermission

ROLE_DEFINITIONS = {
    "SystemAdmin": ["*"],

    "OrgAdmin": [
        "organization.view", "organization.update", "organization.suspend",
        "organization.activate", "organization.archive",
        "enquiry.view", "enquiry.create", "enquiry.update",
        "enquiry.qualify", "enquiry.disqualify", "enquiry.close",
        "followup.view", "followup.create", "followup.update",
        "followup.complete", "followup.cancel",
        "quotation.view", "quotation.create", "quotation.update",
        "quotation.send", "quotation.accept", "quotation.reject", "quotation.expire",
        "role.view",
    ],

    "SalesManager": [
        "enquiry.view", "enquiry.create", "enquiry.update",
        "enquiry.qualify", "enquiry.disqualify", "enquiry.close",
        "followup.view", "followup.create", "followup.update",
        "followup.complete", "followup.cancel",
        "quotation.view", "quotation.create",
        "quotation.send", "quotation.accept", "quotation.reject",
    ],

    "SalesExecutive": [
        "enquiry.view", "enquiry.create", "enquiry.update",
        "enquiry.qualify", "enquiry.disqualify",
        "followup.view", "followup.create", "followup.update",
        "quotation.view", "quotation.create", "quotation.send",
    ],

    "FinanceUser": [
        "quotation.view", "quotation.accept", "quotation.reject",
    ],

    "ReadOnlyUser": [
        "organization.view", "enquiry.view", "followup.view", "quotation.view",
    ],
}


class Command(BaseCommand):
    help = "Seed global roles and permissions"

    def handle(self, *args, **options):
        permissions = {
            p.code: p for p in Permission.objects.all()
        }

        for role_name, perm_codes in ROLE_DEFINITIONS.items():
            role, _ = Role.objects.get_or_create(name=role_name)

            if perm_codes == ["*"]:
                for perm in permissions.values():
                    RolePermission.objects.get_or_create(
                        role=role, permission=perm
                    )
                continue

            for code in perm_codes:
                perm = permissions.get(code)
                if not perm:
                    self.stderr.write(f"Missing permission: {code}")
                    continue

                RolePermission.objects.get_or_create(
                    role=role,
                    permission=perm,
                )

        self.stdout.write(self.style.SUCCESS("Roles & permissions seeded."))
