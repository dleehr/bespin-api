#!/usr/bin/env bash

export DATABASE_URL="postgres://bespindev:throwawaypassword@localhost/bespin_dev"
export BESPIN_SECRET_KEY=dummy-dev-key
export DJANGO_SETTINGS_MODULE=bespin.settings

python manage.py migrate
python manage.py runserver

