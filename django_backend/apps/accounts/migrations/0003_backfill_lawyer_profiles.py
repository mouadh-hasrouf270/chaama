from django.db import migrations


def create_profiles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    LawyerProfile = apps.get_model('accounts', 'LawyerProfile')
    alias = schema_editor.connection.alias
    for user in User.objects.using(alias).filter(role__in=['INTERNAL_ASSOCIATE', 'EXTERNAL_SUBCONTRACTOR']).iterator():
        LawyerProfile.objects.using(alias).get_or_create(user_id=user.pk)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0002_practicearea_user_phone_user_phone_verified_client_and_more')]
    operations = [migrations.RunPython(create_profiles, migrations.RunPython.noop)]
