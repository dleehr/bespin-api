#!/usr/bin/env bash

export DATABASE_URL="postgres://bespinprod:throwawaypassword@localhost/bespin_prod"
export BESPIN_SECRET_KEY=dummy-prod-key
export DJANGO_SETTINGS_MODULE=bespin.settings_prod

python manage.py migrate
python manage.py collectstatic
gunicorn -b 0.0.0.0:8000 bespin.wsgi:application --log-level=debug

