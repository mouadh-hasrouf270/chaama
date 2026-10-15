from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('appointments', '0002_bookingrequest')]
    operations = [migrations.AddField(model_name='bookingrequest', name='appointment', field=models.OneToOneField(to='appointments.appointment', null=True, blank=True, on_delete=django.db.models.deletion.PROTECT, related_name='source_request'))]
