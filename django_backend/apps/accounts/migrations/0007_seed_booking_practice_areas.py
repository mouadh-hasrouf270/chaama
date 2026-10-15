from django.db import migrations

DEFAULT_AREAS = [
    ('Droit civil', 'droit-civil'),
    ('Droit pénal', 'droit-penal'),
    ('Droit de la famille', 'droit-famille'),
    ('Droit commercial', 'droit-commercial'),
    ('Droit du travail', 'droit-travail'),
    ('Droit immobilier', 'droit-immobilier'),
    ('Droit administratif', 'droit-administratif'),
    ('Autre domaine juridique', 'autre-domaine-juridique'),
]

def seed_areas(apps, schema_editor):
    Area = apps.get_model('accounts', 'PracticeArea')
    db = schema_editor.connection.alias
    for name, slug in DEFAULT_AREAS:
        if not Area.objects.using(db).filter(slug=slug).exists() and not Area.objects.using(db).filter(name=name).exists():
            Area.objects.using(db).create(name=name, slug=slug, is_active=True)

class Migration(migrations.Migration):
    dependencies = [('accounts', '0006_sync_admin_access')]
    operations = [migrations.RunPython(seed_areas, migrations.RunPython.noop)]
