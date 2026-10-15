
#!/usr/bin/env bash
set -euo pipefail

python -m pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py migrate --noinput

if [[ -n "${INITIAL_ADMIN_USERNAME:-}" && \
      -n "${INITIAL_ADMIN_EMAIL:-}" && \
      -n "${INITIAL_ADMIN_PASSWORD:-}" ]]; then
    python manage.py create_initial_superuser
fi

python manage.py check --deploy
