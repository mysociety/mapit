#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd "$(dirname $BASH_SOURCE)"/..

# Some env variables used during development seem to make things break - set
# them back to the defaults which is what they would have on the servers.
PYTHONDONTWRITEBYTECODE=""

# create the virtual environment
virtualenv_dir='../virtualenv-mapit'
virtualenv_activate="$virtualenv_dir/bin/activate"

if [ ! -f "$virtualenv_activate" ]
then
    python3 -m venv $virtualenv_dir
fi

source $virtualenv_activate

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
