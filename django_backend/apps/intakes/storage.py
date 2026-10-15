from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateEvidenceStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.PRIVATE_EVIDENCE_ROOT)

    def url(self, name):
        raise ValueError('Private files are available only through authorized downloads.')


def evidence_path(instance, filename):
    return f'intakes/{instance.intake_id}/{uuid4().hex}{Path(filename).suffix.lower()}'

