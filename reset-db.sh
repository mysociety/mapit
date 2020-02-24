#!/usr/bin/env bash

set -ex

psql -U postgres -c "DROP DATABASE mapit;"
createdb -U postgres --owner mapit mapit
psql -U postgres -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;" mapit
python ./manage.py migrate -v 0
