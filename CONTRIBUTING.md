# Contributing

## Quick local setup

You will need [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
and [Vagrant](https://www.vagrantup.com/docs/installation/).

Clone this repo:

    git clone git@github.com:mysociety/mapit.git
    cd mapit

Create, and SSH in to, the Vagrant VM:

    vagrant up
    vagrant ssh

Inside the VM, run the Django dev server:

    cd /vagrant/mapit
    ./manage.py runserver 0.0.0.0:8000

MapIt will be accessible at <http://localhost:8000> on the host machine.

If you make changes to the stylesheets, you will need to recompile the Sass
files, using the `bin/mapit_make_css` script (on your host if you want the map
to update).

## Full setup on your own server

See <http://code.mapit.mysociety.org/>
