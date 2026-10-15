from django.db import migrations


def seed(apps, schema_editor):
    apps.get_model('calendar_app', 'PracticeArea').objects.get_or_create(
        slug='consultation-generale', defaults={'name': 'Consultation générale'})


class Migration(migrations.Migration):
    dependencies = [('calendar_app', '0002_practicearea_appointment')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
