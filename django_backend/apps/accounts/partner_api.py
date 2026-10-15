import secrets
import string
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import PartnerApplication, User, LawyerProfile
from .permissions import IsSuperAdmin

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerApplication
        fields = ['id','full_name','cabinet','email','phone','bar_number','jurisdiction','specialties','status','created_at','reviewed_at','account']
        read_only_fields = fields

@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def apply(request):
    d = request.data
    required = ['full_name','cabinet','email','phone','bar_number','jurisdiction']
    missing = [k for k in required if not str(d.get(k,'')).strip()]
    if missing: return Response({'detail':'Champs requis : '+', '.join(missing)},status=400)
    email = str(d['email']).strip().lower()
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try: validate_email(email)
    except ValidationError: return Response({'detail':'Adresse email invalide.'},status=400)
    from .services import normalize_phone
    try: phone = normalize_phone(d['phone'])
    except ValidationError: return Response({'detail':'Numéro de téléphone invalide.'},status=400)
    if not phone: return Response({'detail':'Numéro de téléphone invalide.'},status=400)
    proof = request.FILES.get('proof')
    if not proof or proof.size > 5*1024*1024 or proof.name.rsplit('.',1)[-1].lower() not in ('pdf','jpg','jpeg','png'):
        return Response({'detail':'Justificatif PDF/JPG/PNG obligatoire (5 Mo maximum).'},status=400)
    magic = proof.read(8); proof.seek(0)
    if not (magic.startswith(b'%PDF-') or magic.startswith(b'\xff\xd8\xff') or magic.startswith(b'\x89PNG\r\n\x1a\n')):
        return Response({'detail':'Format du fichier non reconnu.'},status=400)
    import json
    try: specialties=json.loads(d.get('specialties','[]'))
    except (ValueError,TypeError): specialties=[]
    if not isinstance(specialties,list) or not specialties or any(not isinstance(x,str) or len(x)>100 for x in specialties):
        return Response({'detail':'Sélectionnez au moins une spécialité.'},status=400)
    if PartnerApplication.objects.filter(email__iexact=email,status='PENDING').exists():
        return Response({'detail':'Une demande est déjà en cours pour cette adresse.'},status=409)
    record=PartnerApplication.objects.create(full_name=d['full_name'].strip()[:200],cabinet=d['cabinet'].strip()[:200],email=email,phone=phone,bar_number=d['bar_number'].strip()[:100],jurisdiction=d['jurisdiction'].strip()[:150],specialties=specialties,proof=proof)
    return Response({'id':record.id,'status':'PENDING'},status=201)

@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def applications(request):
    rows=PartnerApplication.objects.all().order_by('-created_at')[:250]
    return Response(ApplicationSerializer(rows,many=True).data)

@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def proof(request,pk):
    from django.shortcuts import get_object_or_404
    record=get_object_or_404(PartnerApplication,pk=pk)
    if not record.proof: return Response({'detail':'Aucun document'},status=404)
    return FileResponse(record.proof.open('rb'),as_attachment=True,filename=record.proof.name.rsplit('/',1)[-1])

@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def decide(request,pk):
    decision=request.data.get('decision')
    if decision not in ('approve','reject'): return Response({'detail':'Décision invalide.'},status=400)
    with transaction.atomic():
        from django.shortcuts import get_object_or_404
        app=get_object_or_404(PartnerApplication.objects.select_for_update(),pk=pk)
        if app.status != 'PENDING': return Response({'detail':'Cette demande a déjà été traitée.'},status=409)
        if decision == 'reject':
            app.status='REJECTED'; app.reviewed_by=request.user; app.reviewed_at=timezone.now(); app.save(update_fields=['status','reviewed_by','reviewed_at'])
            return Response({'status':'REJECTED'})
        if User.objects.filter(email__iexact=app.email).exists():
            return Response({'detail':'Un compte utilise déjà cet email. Vérifiez-le manuellement.'},status=409)
        username='partner'+str(app.pk)
        while User.objects.filter(username=username).exists(): username='partner'+str(app.pk)+'_'+secrets.token_hex(3)
        alphabet=string.ascii_letters+string.digits+'!@#%-_'
        password=''.join(secrets.choice(alphabet) for _ in range(20))
        names=app.full_name.split(' ',1)
        user=User(username=username,email=app.email,first_name=names[0],last_name=names[1] if len(names)>1 else '',role=User.Role.EXTERNAL_SUBCONTRACTOR,is_active=True)
        user.set_password(password)
        user.save()
        LawyerProfile.objects.update_or_create(user=user,defaults={'bar_number':app.bar_number,'jurisdiction':app.jurisdiction,'is_verified':True})
        app.status='APPROVED'; app.account=user; app.reviewed_by=request.user; app.reviewed_at=timezone.now(); app.save(update_fields=['status','account','reviewed_by','reviewed_at'])
        return Response({'status':'APPROVED','username':username,'temporary_password':password,'phone':app.phone,'note':'Copiez ces identifiants maintenant : le mot de passe ne sera plus affiché.'})

@api_view(['GET'])
@permission_classes([AllowAny])
def public_stats(request):
    from django.db.models import Max
    from apps.practice.models import Matter
    verified = LawyerProfile.objects.filter(is_verified=True, user__is_active=True)
    experience = verified.aggregate(value=Max('years_experience'))['value']
    # Aucune donnée de satisfaction certifiée : ne pas inventer un nombre.
    return Response({'years_experience':experience,'matters_count':Matter.objects.filter(status='CLOSED').count(), 'satisfied_clients':None,'verified_lawyers':verified.count()})
