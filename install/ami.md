---
layout: page
title: MapIt AMI for EC2
---

# MapIt AMI for EC2

To help people to get started with MapIt, we have
created an AMI (Amazon Machine Image) with a basic installation of
MapIt, which you can use to create a running server on an Amazon
EC2 instance.

If you haven't used Amazon Web Services before, then you can get a
Micro instance which will be [free for a
year](http://aws.amazon.com/free/).

The AMI can be found in the **EU West (Ireland)** region, with the ID
`ami-2099e353` and name "MapIt installation 2016-09-22".
You can launch an instance based on that AMI with
[this link](https://console.aws.amazon.com/ec2/home?region=eu-west-1#launchAmi=ami-2099e353).

When you create an EC2 instance based on that AMI, make sure that you
choose Security Groups that allows at least inbound HTTP, HTTPS and
SSH.

When your EC2 instance is launched, you will be able to log in as the
`ubuntu` user.  This user can `sudo` freely to run commands as root.
However, the code is actually owned by (and runs as) the `mapit` user.
After creating the instance, you may want to edit a configuration
file to set a couple of parameters.  That configuration file is
`/home/mapit/mapit/conf/general.yml`, which can be edited with:

    ubuntu@ip-10-58-191-98:~$ sudo su - mapit
    mapit@ip-10-58-191-98:~$ cd mapit
    mapit@ip-10-58-191-98:~/mapit$ nano conf/general.yml

You should set `BUGS_EMAIL` to your email address.  You should also
consider the `AREA_SRID` and `COUNTRY` settings, as described in the
[manual installation instructions](/install/).

Note if you change the SRID at this point, you will need to revert and then
re-migrate the database as it will already have been set up with the initial
SRID:

    source ../virtualenv-mapit/bin/activate
    ./manage.py migrate mapit zero
    ./manage.py migrate mapit

Then you should then restart the MapIt Django server with:

    mapit@ip-10-58-191-98:~/mapit$ logout
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
