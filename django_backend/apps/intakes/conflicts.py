import re
import unicodedata
from apps.accounts.models import Client


def normalize_party_name(value):
    value = unicodedata.normalize('NFKD', value).casefold()
    value = ''.join(c for c in value if not unicodedata.combining(c))
    return re.sub(r'[^\w\s]', ' ', value).strip()


def search_existing_parties(name, exclude_intake=None, exclude_assistance=None):
    # Extend these sources later with MatterParty; never return matched private
    # records to clients or external lawyers.
    from .models import Intake
    from apps.assistance.models import AssistanceRequest
    needle = ' '.join(normalize_party_name(name).split())
    if not needle:
        return []
    clients = (f'{first} {last}' for first, last in Client.objects.values_list('first_name', 'last_name').iterator())
    intakes = Intake.objects.exclude(pk=exclude_intake).values_list('opposing_party', flat=True).iterator()
    assistance = AssistanceRequest.objects.exclude(pk=exclude_assistance).values_list('opposing_party', flat=True).iterator()
    matches = []
    for source, names in [('client', clients), ('intake', intakes), ('assistance', assistance)]:
        for existing in names:
            normalized = ' '.join(normalize_party_name(existing).split())
            if normalized == needle:
                matches.append(source)
                break
    return matches


def flag_possible_conflict(name, **kwargs):
    if not normalize_party_name(name):
        return 'REVIEW_REQUIRED'
    return 'POSSIBLE_MATCH' if search_existing_parties(name, **kwargs) else 'NO_MATCH'

