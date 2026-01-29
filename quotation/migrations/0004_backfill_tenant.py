from django.db import migrations


def backfill_tenant(apps, schema_editor):
    Tenant = apps.get_model("core", "Tenant")
    Quotation = apps.get_model("quotation", "Quotation")

    default_tenant = Tenant.objects.first()
    Quotation.objects.filter(tenant__isnull=True).update(tenant=default_tenant)
class Migration(migrations.Migration):

    dependencies = [
        ("quotation", "0003_alter_quotation_options_quotation_tenant_and_more"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_tenant),
    ]
