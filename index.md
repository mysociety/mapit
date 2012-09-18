---
layout: default
title: Welcome
---

Welcome to MapIt
================

MapIt is a web service that maps geographical points to administrative areas.
It is useful for anyone who has the co-ordinates of a point on Earth, and who
needs to find out what country, region, city, constituency, or state it lies
within. It’s also great for looking up the shapes of all those boundaries.

**This site is about how to install your own copy of MapIt on your own server,
and how to import data into it.** [mySociety][] (the UK charity that wrote this
code) runs public installations of MapIt that you might be able to use:

* [MapIt Global] &ndash; global boundaries from the [OpenStreetMap] project.
* [MapIt UK] &ndash; UK boundaries from various sources.

The above are free for non-commercial, low-volume use.

Technical Overview
------------------

The `mapit` directory contains a standard [GeoDjango] app, and the `project`
directory contains an example GeoDjango project using that app. Other top-level
things are mostly to fit within mySociety's standard deployment, or country
specific data, one-off scripts and so on.

MapIt has been installed on Debian lenny and squeeze, and on Ubuntu from 10.04
onwards. If GeoDjango and [PostGIS] run on it, it should theoretically be okay;
do let us know of any problems.

Installation
------------

MapIt can be installed as a Django app, or as a standalone server. For full
details, see the [installation documentation](install/).

Importing data
--------------

There are various ways to import data into MapIt, ranging from manually to
importing KML files. We have also supplied notes for some of the countries
that MapIt has been set up for; see the links in the navigation.

Contact
-------

Improvements, patches, questions and comments are all welcome. The code is
hosted on GitHub and we use their bug tracker too, so please open a ticket
there:

* GitHub home: <https://github.com/mysociety/mapit>
* GitHub issues: <https://github.com/mysociety/mapit/issues>

You can also chat to us on IRC: #mschat on [irc.mysociety.org](http://www.irc.mysociety.org).

[mySociety]: http://www.mysociety.org/
[MapIt Global]: http://global.mapit.mysociety.org/
[MapIt UK]: http://mapit.mysociety.org/
[OpenStreetMap]: http://www.openstreetmap.org/
[GeoDjango]: http://geodjango.org/
[PostGIS]: http://postgis.refractions.net/

