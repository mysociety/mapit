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

virtualenv_dir='../virtualenv-mapit'
virtualenv_activate="$virtualenv_dir/bin/activate"

if [ ! -f "$virtualenv_activate" ]
then
    virtualenv $virtualenv_args $virtualenv_dir
fi

source $virtualenv_activate

# Upgrade pip to a secure version
# curl -L -s https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python
# Revert to the line above once we can get a newer setuptools from Debian, or
# pip ceases to need such a recent one.
curl -L -s https://raw.github.com/mysociety/commonlib/master/bin/get_pip.bash | bash

# Install all the packages
pip install -e .

# make sure that there is no old code (the .py files may have been git deleted) 
find . -name '*.pyc' -delete

# Compile CSS
bin/mapit_make_css

# get the database up to speed
python manage.py migrate

# gather all the static files in one place
python manage.py collectstatic --noinput
