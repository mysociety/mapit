#!/usr/bin/env bash

set -e

DIRECTORY='.venv'
if [ ! -d "$DIRECTORY" ]; then
  virtualenv -p python3 --no-site-packages "$DIRECTORY"
fi

$DIRECTORY/bin/python -m pip install --upgrade pip wheel setuptools
$DIRECTORY/bin/python -m pip install -r requirements.txt
$DIRECTORY/bin/python manage.py migrate -v 0
$DIRECTORY/bin/python manage.py runserver 3108
