from django.db import migrations


def backfill(apps, schema_editor):
    Matter = apps.get_model('matters', 'Matter')
    Client = apps.get_model('matters', 'Client')
    for matter in Matter.objects.filter(client__isnull=False).select_related('client').iterator():
        user = matter.client
        profile, _ = Client.objects.get_or_create(user_id=user.pk, defaults={
            'first_name': user.first_name or user.username, 'last_name': user.last_name,
            'email': user.email, 'created_by_id': matter.created_by_id,
        })
        matter.client_profile_id = profile.pk
        matter.save(update_fields=['client_profile'])


class Migration(migrations.Migration):
    dependencies = [('matters', '0002_matter_version_alter_matter_client_client_and_more')]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
