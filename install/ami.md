---
layout: default
title: AMI for EC2
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
`ami-639f9e17` and name "Basic MapIt installation 2012-10-01".

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
consider the `SRID` and `COUNTRY` settings, as described in the
[manual installation instructions](/install/).

Then you should then restart the MapIt Django server with:

    mapit@ip-10-58-191-98:~/mapit$ logout
    ubuntu@ip-10-58-191-98:~$ sudo /etc/init.d/mapit restart

Now you will probably want to carry on to [import some data](import).
