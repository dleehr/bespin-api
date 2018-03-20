#!/usr/bin/env bash

export DATABASE_URL="postgres://bespinprod:throwawaypassword@localhost/bespin_prod"
export BESPIN_SECRET_KEY=dummy-prod-key
export DJANGO_SETTINGS_MODULE=bespin.settings_prod

docker run \
  -e DATABASE_URL="postgres://bespinprod:throwawaypassword@localhost/bespin_prod" \
  -e BESPIN_SECRET_KEY=dummy-prod-key \
  -e DJANGO_SETTINGS_MODULE=bespin.settings_prod \
  -it \
  bespin-api

