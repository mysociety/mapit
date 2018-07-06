#!/bin/bash
set -e

VENV_PATH="${HOME}/venv/${JOB_NAME}"

[ -x ${VENV_PATH}/bin/pip ] || virtualenv ${VENV_PATH}
. ${VENV_PATH}/bin/activate

pip install -q ghtools

REPO="alphagov/mapit"
gh-status "$REPO" "$GIT_COMMIT" pending -d "\"Build #${BUILD_NUMBER} is running on Jenkins\"" -u "$BUILD_URL" >/dev/null

if ./jenkins.sh; then
  gh-status "$REPO" "$GIT_COMMIT" success -d "\"Build #${BUILD_NUMBER} succeeded on Jenkins\"" -u "$BUILD_URL" >/dev/null
  exit 0
else
  gh-status "$REPO" "$GIT_COMMIT" failure -d "\"Build #${BUILD_NUMBER} failed on Jenkins\"" -u "$BUILD_URL" >/dev/null
  exit 1
fi
