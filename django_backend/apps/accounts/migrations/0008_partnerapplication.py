from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('accounts','0007_seed_booking_practice_areas'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='PartnerApplication', fields=[
        ('id',models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('full_name',models.CharField(max_length=200)), ('cabinet',models.CharField(max_length=200)),
        ('email',models.EmailField(max_length=254)), ('phone',models.CharField(max_length=35)),
        ('bar_number',models.CharField(max_length=100)), ('jurisdiction',models.CharField(max_length=150)),
        ('specialties',models.JSONField(default=list)),
        ('proof',models.FileField(upload_to='partner_proofs/%Y/%m/')),
        ('status',models.CharField(choices=[('PENDING','En attente'),('APPROVED','Acceptée'),('REJECTED','Refusée')],default='PENDING',max_length=12)),
        ('created_at',models.DateTimeField(auto_now_add=True)), ('reviewed_at',models.DateTimeField(blank=True,null=True)),
        ('account',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='partner_applications',to=settings.AUTH_USER_MODEL)),
        ('reviewed_by',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='partner_reviews',to=settings.AUTH_USER_MODEL)),
    ],options={'ordering':['-created_at']})]
