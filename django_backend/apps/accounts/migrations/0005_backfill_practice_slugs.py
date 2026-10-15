from django.db import migrations, models
from django.utils.text import slugify


def backfill_slugs(apps, schema_editor):
    PracticeArea = apps.get_model('accounts', 'PracticeArea')
    for area in PracticeArea.objects.using(schema_editor.connection.alias).filter(slug__isnull=True).iterator():
        area.slug = f'{slugify(area.name)[:140] or "practice"}-{area.pk}'
        area.save(update_fields=['slug'])


class Migration(migrations.Migration):
    dependencies = [('accounts', '0004_lawyerprofile_availability_status_and_more')]
    operations = [
        migrations.RunPython(backfill_slugs, migrations.RunPython.noop),
        migrations.AlterField('practicearea', 'slug', models.SlugField(max_length=180, unique=True, blank=True)),
    ]
