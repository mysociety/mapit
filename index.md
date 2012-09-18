---
layout: default
title: Welcome
---

MapIt
=====

MapIt is a service that maps geographical points to administrative areas. It is
useful for anyone who has the co-ordinates of a point on Earth, and who needs
to find out what country, region, city, constituency, or state it lies within.
It’s also great for looking up the shapes of all those boundaries.

[mySociety][] (the UK charity that wrote this code) runs several public MapIts
that you can use:

* [MapIt Global] - global boundaries from the [OSM] project.
* [MapIt UK] - UK boundaries from various sources.

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

MapIt can be installed as a Django app, or as a standalone server. Full details
are in `INSTALL.rst`.

Country specific READMEs
------------------------

These are extensive notes for some of the countries that MapIt has been set up
to serve. These are in the `docs` folder:

* UK: `docs/README-UK.rst`
* Norway: `docs/README-NORWAY.rst`

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
[OSM]: http://www.openstreetmap.org/
[GeoDjango]: http://geodjango.org/
[PostGIS]: http://postgis.refractions.net/

