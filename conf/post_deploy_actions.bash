#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd "$(dirname $BASH_SOURCE)"/..

# Some env variables used during development seem to make things break - set
# them back to the defaults which is what they would have on the servers.
PYTHONDONTWRITEBYTECODE=""

# create the virtual environment; we always want system packages
virtualenv_version="$(virtualenv --version)"
virtualenv_args=""
if [ "$(echo -e '1.7\n'$virtualenv_version | sort -V | head -1)" = '1.7' ]; then
    virtualenv_args="--system-site-packages"
fi
virtualenv $virtualenv_args ../virtualenv-mapit
source ../virtualenv-mapit/bin/activate

# Upgrade pip to a secure version
if [ -f /data/mysociety/bin/get-pip.py ]; then
    python /data/mysociety/bin/get-pip.py
else
    curl -s https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python
fi

# Install all the packages
pip install -r requirements.txt

# make sure that there is no old code (the .py files may have been git deleted) 
find . -name '*.pyc' -delete

# Compile CSS
bin/mapit_make_css

# get the database up to speed
python manage.py syncdb --noinput
python manage.py migrate

# gather all the static files in one place
python manage.py collectstatic --noinput
