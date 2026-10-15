from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('appointments', '0001_initial'), ('accounts', '0007_seed_booking_practice_areas')]
    operations = [migrations.CreateModel(name='BookingRequest', fields=[
        ('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
        ('full_name', models.CharField(max_length=200)),
        ('email', models.EmailField(max_length=254)),
        ('phone', models.CharField(max_length=32)),
        ('legal_topic', models.CharField(max_length=200)),
        ('description', models.TextField()),
        ('opposing_party', models.CharField(max_length=250, blank=True)),
        ('requested_date', models.DateField()),
        ('preferred_time', models.TimeField()),
        ('consultation_type', models.CharField(max_length=10, choices=[('OFFICE', 'Office'), ('VIDEO', 'Video'), ('PHONE', 'Phone')])),
        ('status', models.CharField(max_length=12, choices=[('NEW', 'New'), ('CONTACTED', 'Contacted'), ('CONVERTED', 'Converted to appointment'), ('CLOSED', 'Closed')], default='NEW')),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('updated_at', models.DateTimeField(auto_now=True)),
        ('client', models.ForeignKey(to='accounts.client', null=True, blank=True, related_name='booking_requests', on_delete=django.db.models.deletion.SET_NULL)),
        ('practice_area', models.ForeignKey(to='accounts.practicearea', on_delete=django.db.models.deletion.PROTECT)),
    ], options={'ordering': ['-created_at']})]
