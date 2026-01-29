from django.db import migrations


def seed_modules(apps, schema_editor):
    Module = apps.get_model("core", "Module")

    modules = [
        {"code": "organization", "name": "Organization"},
        {"code": "enquiry", "name": "Enquiry"},
        {"code": "followup", "name": "Follow-up"},
        {"code": "quotation", "name": "Quotation"},
    ]

    for module in modules:
        Module.objects.get_or_create(
            code=module["code"],
            defaults={"name": module["name"]},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_modules),
    ]
