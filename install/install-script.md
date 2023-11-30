---
layout: page
title: MapIt install script
---

# MapIt Install Script

If you have a new installation of Debian (Buster or Bullseye) or Ubuntu Focal,
you can use an install script to set up a basic installation of
MapIt on your server.


**Please note that the install script does not currently work on Ubuntu Jammy.**

<div class="attention-box">
<strong>Warning:</strong> only use this script on a newly installed server - it will
make significant changes to your server's setup, including modifying
your nginx setup, creating a user account, creating a database,
installing new packages etc.
</div>

The script to run is called [`install-site.sh`, in our `commonlib` repository](https://github.com/mysociety/commonlib/raw/master/bin/install-site.sh).
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

{% highlight bash %}
curl -L -O https://github.com/mysociety/commonlib/raw/master/bin/install-site.sh
sudo sh install-site.sh mapit mapit mapit.example.org
{% endhighlight %}

Or, if you want to set this up as the default site on an EC2 instance,
you could download the script, make it executable and then invoke it
as:

    sudo ./install-site.sh --default mapit mapit

When the script has finished, you should have a working copy of the
website, accessible via the hostname you supplied to the script.

You should take a look at the configuration file in
`mapit/conf/general.yml` under `/var/www/<host>`. In particular, you should set `BUGS_EMAIL`
to your email address.  You should also consider the `AREA_SRID` and
`COUNTRY` settings, as described in the [manual installation
instructions](/install/).

Note if you change the SRID at this point, you will need to revert and then
re-migrate the database as it will already have been set up with the initial
SRID:

    source ../virtualenv-mapit/bin/activate
    ./manage.py migrate mapit zero
    ./manage.py migrate mapit

Then you should then restart the MapIt Django server with:

    ubuntu@ip-10-58-191-98:~$ sudo /etc/init.d/mapit restart

You will need to create an admin user if you want to be able to use
MapIt's web admin interface.  To create an admin user, you need to use
the `createsuperuser` Django admin command, similar to the following
example:

    ubuntu@ip-10-64-6-199:~$ sudo su - mapit
    mapit@ip-10-64-6-199:~$ cd /var/www/mapit/mapit
    mapit@ip-10-64-6-199:~/mapit$ source ../virtualenv-mapit/bin/activate
    (mapit)mapit@ip-10-64-6-199:~/mapit$ ./manage.py createsuperuser
    Username (Leave blank to use 'mapit'): mapitadmin
    E-mail address: whoever@example.org
    Password:
    Password (again):
    Superuser created successfully.

... and check that you can now login to the admin interface by
visiting `/admin` on your site.

Now you will probably want to carry on to [import some data](/import/).
