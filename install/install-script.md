---
layout: default
title: Install script
---

# MapIt Install Script

If you have a new installation of Debian squeeze or Ubuntu precise,
you can use an install script to set up a basic installation of
MapIt on your server.

*Warning: only use this script on a newly installed server - it will
make significant changes to your server's setup, including modifying
your nginx setup, creating a user account, creating a database,
installing new packages etc.*

The script to run is called [`install-site.sh`, in our `commonlib` repository](https://raw.github.com/mysociety/commonlib/master/bin/install-site.sh).
That script's usage is as follows:

    Usage: ./install-site.sh [--default] <SITE-NAME> <UNIX-USER> [HOST]
    HOST is only optional if you are running this on an EC2 instance.
    --default means to install as the default site for this server,
    rather than a virtualhost for HOST.

The `<UNIX-USER>` parameter is the name of the Unix user that you want
to own and run the code.  (This user will be created by the script.)

The `HOST` parameter is a hostname for the server that will be usable
externally - a virtualhost for this name will be created by the
script, unless you specified the `--default` option..  This parameter
is optional if you are on an EC2 instance, in which case the hostname
of that instance will be used.

For example, if you wish to use a new user called `mapit` and the
hostname `mapit.example.org`, creating a virtualhost just for that
hostname, you could download and run the script with:

    curl https://raw.github.com/mysociety/commonlib/master/bin/install-site.sh | \
        sudo sh -s mapit mapit mapit.example.org

Or, if you want to set this up as the default site on an EC2 instance,
you could download the script and then invoke it with:

    sudo ./install-site.sh --default mapit mapit

When the script has finished, you should have a working copy of the
website, accessible via the hostname you supplied to the script.

You should take a look at the configuration file in
`mapit/conf/general.yml`.  In particular, you should set `BUGS_EMAIL`
to your email address.  You should also consider the `SRID` and
`COUNTRY` settings, as described in the [manual installation
instructions](/install/).

Then you should then restart the MapIt Django server with:

    mapit@ip-10-58-191-98:~/mapit$ logout
    ubuntu@ip-10-58-191-98:~$ sudo /etc/init.d/mapit restart

You will need to create an admin user if you want to be able to use
MapIt's web admin interface.  To create an admin user, you need to use
the `createsuperuser` Django admin command, similar to the following
example:

    ubuntu@ip-10-64-6-199:~$ sudo su - mapit
    mapit@ip-10-64-6-199:~$ cd mapit/project/
    mapit@ip-10-64-6-199:~/mapit/project$ ./manage.py createsuperuser
    Username (Leave blank to use 'mapit'): mapitadmin
    E-mail address: whoever@example.org
    Password:
    Password (again):
    Superuser created successfully.

... and check that you can now login to the admin interface by
visiting `/admin` on your site.

Now you will probably want to carry on to [import some data](import).
