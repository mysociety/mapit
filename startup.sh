#!/bin/bash
set -e

DIRECTORY='.venv'
if [ ! -d "$DIRECTORY" ]; then
  virtualenv --no-site-packages "$DIRECTORY"
fi

$DIRECTORY/bin/pip install --upgrade pip wheel setuptools
$DIRECTORY/bin/pip install -r requirements.txt
$DIRECTORY/bin/python ./manage.py migrate -v 0
$DIRECTORY/bin/python ./manage.py runserver 3108
