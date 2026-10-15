from django.db import migrations


def sync_admin_access(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    users = User.objects.using(schema_editor.connection.alias)
    users.filter(is_superuser=True, role='CLIENT').update(role='SUPER_ADMIN')
    users.filter(role='SUPER_ADMIN').update(is_staff=True, is_superuser=True)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0005_backfill_practice_slugs')]
    operations = [migrations.RunPython(sync_admin_access, migrations.RunPython.noop)]
