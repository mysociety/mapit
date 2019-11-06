#!/usr/bin/env bash

set -ex

sudo -u postgres dropdb mapit
sudo -u postgres createdb --owner mapit mapit
sudo -u postgres psql -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;" mapit
govuk_setenv mapit .venv/bin/python manage.py migrate
