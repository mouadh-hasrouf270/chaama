from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('practice', '0001_initial'), ('appointments', '0002_bookingrequest')]
    operations = [migrations.CreateModel(name='GoogleAppointmentLink', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('google_event_id', models.CharField(max_length=255)),
        ('appointment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appointments.appointment')),
        ('connection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='practice.googlecalendarconnection')),
    ], options={'constraints': [models.UniqueConstraint(fields=('connection', 'appointment'), name='unique_google_client_appointment')]} )]
