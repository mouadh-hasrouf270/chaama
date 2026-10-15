from django.db import migrations, models


def forwards(apps, schema_editor):
    apps.get_model('organizations', 'Organization').objects.filter(type='CH2MA').update(type='CHAAMA')


def backwards(apps, schema_editor):
    apps.get_model('organizations', 'Organization').objects.filter(type='CHAAMA').update(type='CH2MA')


class Migration(migrations.Migration):
    dependencies = [('organizations', '0001_initial')]
    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(model_name='organization', name='type', field=models.CharField(
            max_length=20, choices=[('CHAAMA', 'Chaama'), ('PARTNER_FIRM', 'Partner firm')]))
    ]
