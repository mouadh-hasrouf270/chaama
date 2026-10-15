from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import FileExtensionValidator
import apps.practice.models as practice_models

class Migration(migrations.Migration):
    initial = True
    dependencies = [('accounts','0006_sync_admin_access'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Matter', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('client', models.ForeignKey('accounts.Client', on_delete=models.PROTECT, related_name='matters')),
            ('reference', models.CharField(max_length=32, unique=True, editable=False)),
            ('title', models.CharField(max_length=250)),
            ('matter_type', models.CharField(max_length=120, blank=True)),
            ('description', models.TextField(blank=True)),
            ('opposing_party', models.CharField(max_length=250, blank=True)),
            ('jurisdiction', models.CharField(max_length=180, blank=True)),
            ('court_reference', models.CharField(max_length=140, blank=True)),
            ('status', models.CharField(max_length=20, choices=[('OPEN','Ouvert'),('IN_PROGRESS','En cours'),('ON_HOLD','En attente'),('CLOSED','Clôturé')], default='OPEN')),
            ('opened_at', models.DateField()),
            ('closed_at', models.DateField(null=True, blank=True)),
            ('lead_lawyer', models.ForeignKey('accounts.LawyerProfile', on_delete=models.SET_NULL, null=True, blank=True)),
            ('created_by', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_matters')),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
        ]),
        migrations.CreateModel(name='MatterDocument', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('matter', models.ForeignKey('practice.Matter', on_delete=models.CASCADE, related_name='documents')),
            ('title', models.CharField(max_length=200)),
            ('file', models.FileField(upload_to=practice_models.evidence_path, validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xlsx', 'txt'])])),
            ('category', models.CharField(max_length=80, blank=True)),
            ('uploaded_by', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)),
            ('uploaded_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='MatterEvent', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('matter', models.ForeignKey('practice.Matter', on_delete=models.CASCADE, related_name='events')),
            ('title', models.CharField(max_length=220)),
            ('kind', models.CharField(max_length=20, choices=[('HEARING','Audience'),('DEADLINE','Échéance'),('MEETING','Réunion'),('OTHER','Autre')], default='OTHER')),
            ('start_at', models.DateTimeField()),
            ('end_at', models.DateTimeField()),
            ('location', models.CharField(max_length=250, blank=True)),
            ('notes', models.TextField(blank=True)),
            ('created_by', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='MatterNote', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('matter', models.ForeignKey('practice.Matter', on_delete=models.CASCADE, related_name='notes')),
            ('body', models.TextField()),
            ('created_by', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='Invoice', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('reference', models.CharField(max_length=32, unique=True, editable=False)),
            ('matter', models.ForeignKey('practice.Matter', on_delete=models.PROTECT, related_name='invoices')),
            ('status', models.CharField(max_length=20, choices=[('DRAFT','Brouillon'),('ISSUED','Émise'),('PARTIAL','Partiellement payée'),('PAID','Payée'),('CANCELLED','Annulée')], default='DRAFT')),
            ('issue_date', models.DateField()),
            ('due_date', models.DateField()),
            ('tax_rate', models.DecimalField(max_digits=5, decimal_places=2, default=0)),
            ('currency', models.CharField(max_length=3, default='DZD')),
            ('notes', models.TextField(blank=True)),
            ('created_by', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
        ]),
        migrations.CreateModel(name='InvoiceLine', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('invoice', models.ForeignKey('practice.Invoice', on_delete=models.CASCADE, related_name='lines')),
            ('description', models.CharField(max_length=300)),
            ('quantity', models.DecimalField(max_digits=10, decimal_places=2)),
            ('unit_price', models.DecimalField(max_digits=12, decimal_places=2)),
        ]),
        migrations.CreateModel(name='Payment', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('invoice', models.ForeignKey('practice.Invoice', on_delete=models.PROTECT, related_name='payments')),
            ('amount', models.DecimalField(max_digits=12, decimal_places=2)),
            ('paid_at', models.DateField()),
            ('method', models.CharField(max_length=50)),
            ('reference', models.CharField(max_length=140, blank=True)),
            ('recorded_by', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='GoogleCalendarConnection', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('user', models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='google_calendar_connection')),
            ('encrypted_refresh_token', models.TextField()),
            ('calendar_id', models.CharField(max_length=255, default='primary')),
            ('connected_at', models.DateTimeField(auto_now_add=True)),
        ]),
        migrations.CreateModel(name='GoogleEventLink', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('connection', models.ForeignKey('practice.GoogleCalendarConnection', on_delete=models.CASCADE)),
            ('event', models.ForeignKey('practice.MatterEvent', on_delete=models.CASCADE)),
            ('google_event_id', models.CharField(max_length=255)),
        ]),
        migrations.AddConstraint(model_name='googleeventlink', constraint=models.UniqueConstraint(fields=('connection','event'), name='unique_google_matter_event')),
    ]
