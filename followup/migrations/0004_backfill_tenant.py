from django.db import migrations


def backfill_tenant(apps, schema_editor):
    Tenant = apps.get_model("core", "Tenant")
    FollowUp = apps.get_model("followup", "FollowUp")

    default_tenant = Tenant.objects.first()
    FollowUp.objects.filter(tenant__isnull=True).update(tenant=default_tenant)


class Migration(migrations.Migration):

    dependencies = [
        ("followup", "0003_alter_followup_options_followup_tenant_and_more"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_tenant),
    ]
