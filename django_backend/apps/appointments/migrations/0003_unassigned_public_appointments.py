from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('appointments', '0002_bookingrequest')]
    operations = [migrations.AlterField(model_name='appointment', name='lawyer', field=models.ForeignKey(to='accounts.lawyerprofile', on_delete=django.db.models.deletion.PROTECT, null=True, blank=True, related_name='appointments'))]
