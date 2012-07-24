MapIt
=====

MapIt is a service that maps geographical points to administrative areas. It is
useful for anyone who has the co-ordinates of a point on Earth, and who needs
to find out what country, region, city, constituency, or state it lies within.
It’s also great for looking up the shapes of all those boundaries.

`mySociety <http://www.mysociety.org>`_ (the UK charity that wrote this code)
runs several public MapIts that you can use:

    * `MapIt Global <http://global.mapit.mysociety.org/>`_ - global boundaries
      from the `OSM <http://www.openstreetmap.org/>`_ project.
    * `MapIt UK <http://mapit.mysociety.org/>`_ - UK boundaries from various
      sources.

The above are free for non-commercial, low-volume use.

Technical Overview
------------------

The ``mapit`` directory contains a standard `GeoDjango
<http://geodjango.org/>`_ app, and the ``project`` directory contains an
example GeoDjango project using that app. Other top-level things are mostly to
fit within mySociety's standard deployment, or country specific data, one-off
scripts and so on.

MapIt has been installed on Debian lenny and squeeze, and on Ubuntu from 10.04
onwards. If GeoDjango and `PostGIS <http://postgis.refractions.net/>`_ run on
it, it should theoretically be okay; do let us know of any problems.

Installation
------------

MapIt can be installed as a Django app, or as a standalone server. Full details
are in ``INSTALL.rst``.

Country specific READMEs
------------------------

These are extensive notes for some of the countries that MapIt has been set up
to serve. These are in the ``docs`` folder:

  * UK: ``docs/README-UK.rst``
  * Norway: ``docs/README-NORWAY.rst``

Improvements / patches
----------------------

Are welcome :)

The code is hosted on GitHub and we use their bug tracker too:

    * https://github.com/mysociety/mapit
    * https://github.com/mysociety/mapit/issues
