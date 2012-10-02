---
layout: post
title: Easy Installation
author: matthew
---

Welcome to our new site providing documentation about installing and running
your own copy of MapIt, in the same vein as our
[documentation](http://code.fixmystreet.com/) for the FixMyStreet Platform. We
want to make it as easy as we can for people to reuse our code, and over the
past few weeks we've been working on some things that will hopefully help.

Installing
----------

Firstly, we have created an [AMI](/install/ami/) (Amazon Machine Image)
containing an already set-up basic installation of MapIt. You can use this to
create a running server on an Amazon EC2 instance. If you haven't used Amazon
Web Services before, then you can get a Micro instance free for a year.

If you have your own server, then we have separately released the [install
script](/install/install-script/) that is used to create the AMI, which can be
run on any clean Debian or Ubuntu server to set everything up for you, from
PostGIS to nginx.

If you prefer to do things manually, and already know how to set up your
database, web server, and GeoDjango, this site also contains our
[manual documentation](/install/).

Importing
---------

Secondly, we have generalised and improved upon some [import
scripts](/import/), that can be used to easily import boundaries stored in
Shapefiles or KML files, and CSVs of postal code data, into MapIt. We've
provided a [worked example](/import/gadm/) of boundary importing using some
data from [GADM](http://gadm.org/).


