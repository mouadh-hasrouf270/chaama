from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.accounts.models import User
from apps.activity.services import notify, record_action
from apps.intakes.conflicts import flag_possible_conflict
from .models import AssistanceRequest


def submit_assistance_request(data, request):
    with transaction.atomic():
        warning = flag_possible_conflict(data.get('opposing_party', ''))
        item = AssistanceRequest.objects.create(
            **data, requesting_lawyer=request.user.lawyer_profile,
            conflict_warning=warning,
            status='PENDING' if warning == 'NO_MATCH' else 'CONFLICT_REVIEW')
        admin_ids = User.objects.filter(Q(role='SUPER_ADMIN') | Q(is_superuser=True)).filter(is_active=True).values_list('pk', flat=True)
        notify(admin_ids, 'ASSISTANCE_SUBMITTED', 'Demande de collaboration', f'Demande #{item.pk}')
        record_action(request, 'assistance.submitted', item, {'warning': warning})
        return item


def perform_conflict_review(instance):
    return flag_possible_conflict(instance.opposing_party, exclude_assistance=instance.pk)


def review_assistance(instance, approved, request, acknowledge_conflict=False):
    with transaction.atomic():
        AssistanceRequest.objects.filter(pk=instance.pk).update(updated_at=F('updated_at'))
        item = AssistanceRequest.objects.select_for_update().get(pk=instance.pk)
        if item.status not in ['PENDING', 'CONFLICT_REVIEW']:
            raise ValidationError('This request has already been reviewed.')
        warning = perform_conflict_review(item)
        if approved and warning != 'NO_MATCH' and not acknowledge_conflict:
            raise ValidationError({'acknowledge_conflict': 'Human review of the possible conflict is required.'})
        item.status = 'ACCEPTED' if approved else 'DECLINED'
        item.conflict_warning = warning
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.save()
        record_action(request, 'assistance.reviewed', item, {'status': item.status, 'warning': warning})
        notify([item.requesting_lawyer.user_id], f'ASSISTANCE_{item.status}',
               'Demande examinée', f'Demande #{item.pk}: {item.status}')
        # Future integration point: create_matter_from_assistance_request(item).
        # Matter creation is deliberately outside this phase.
        return item

