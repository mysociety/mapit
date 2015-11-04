#!/bin/sh

export GOVUK_ENV=development
set -e

rm -rf ./test-venv

virtualenv --no-site-packages ./test-venv
echo 'Installing packages...'
./test-venv/bin/pip -q install --download-cache "${HOME}/bundles/${JOB_NAME}" -r requirements.txt

echo 'Running tests...'
./test-venv/bin/python manage.py test

echo 'Done'
rm -rf ./test-venv
exit 0
