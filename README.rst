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

Code Layout
-----------

The ``mapit`` directory is a standard `GeoDjango <http://geodjango.org/>`_ app,
and the ``project`` directory is an example GeoDjango project using that app
Other top-level things are mostly to fit within mySociety's standard
deployment, or country specific data, one-off scripts and so on.

MapIt has been installed on Debian lenny and squeeze, and on Ubuntu from 10.04
onwards. If GeoDjango and PostGIS run on it, it should theoretically be okay;
do let us know of any problems. Commands are intended to be run via the
terminal or over ssh.

Installation
------------

MapIt currently uses Postgres/PostGIS as its database backend - there's no reason 
why e.g. SpatiaLite could not be used successfully, but it has never been tried.

To install GeoDjango and PostGIS, please follow all the standard instructions
(including creating the template) at:

    http://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#ubuntudebian

And anything else you need to set up Django as normal.

[ Note for UK/Ireland: Not only is the PostGIS that is installed missing SRID
900913, as the GeoDjango docs tell you, but both SRID 27700 (British National
Grid) and SRID 29902 (Irish National Grid) can be incorrect (and they're quite
important for this application!). After you've installed and got a PostGIS
template, log in to it and update the proj4text column of SRID 27700 to include
+datum=OSGB36, and update SRID 29902 to have +datum=ire65. This may not be
necessary, depending on your version of PostGIS, but do check. ]

You will also need a couple of other Debian packages, so install them:

::

    sudo apt-get install python-yaml memcached python-memcache git-core

You will also need to be using South to manage schema migrations.

Installation as a Django app
----------------------------

As mapit is a Django app, if you are making a GeoDjango project you can simply
use mapit from within your project like any normal Django app:

    * Make sure it is on sys.path (a packaged install e.g. with 'pip install
      django-mapit' does this for you);
    * Add 'mapit' and 'django.contrib.gis' to your INSTALLED_APPS;
    * Add the following settings to settings.py:
        - MAPIT_AREA_SRID - the SRID of your area data (if in doubt, set to 4326)
        - MAPIT_COUNTRY - used to supply country specific functions (such as postcode
          validation). If you look at the country files in mapit/countries/ you can
          see how to add specialised country-specific functions.
        - MAPIT_RATE_LIMIT - a list of IP addresses or User Agents excluded from rate limiting
    * Set up a path in your main urls.py to point at mapit.urls.
    * run './manage.py syncdb' and './manage.py migrate' to ensure the db is set up

This approach is new, so please let us know if something goes wrong or could be
improved.

Installation standalone with the example project
------------------------------------------------

A standard git clone will get you the repository:

::

    git clone git://github.com/mysociety/mapit.git

Now in a terminal, navigate to the mapit directory you've just cloned.

Copy conf/general.yml-example to conf/general.yml and edit it to point to your
local postgresql database, and edit the other settings as per the documentation
given in that file. If you don't know what SRID to use, delete that line or set
it to 4326. COUNTRY is used for e.g. differing sorts of postcode (zipcode)
validation - if you look at the country files in mapit/countries/ you can see
how to add specialised country-specific functions to validate postcodes etc.

If you're going to be importing big datasets, make sure that DEBUG is False;
otherwise, you'll run out of memory as it tries to remember all the SQL queries made.

Optionally, also turn off escape_string_warning in Postgres' config (unless you
want your server to run out of disc space logging all the errors, as ours did
the first time I imported overnight and didn't realise).

At this stage, you should be able to set up the database and run the
development server. Do add an admin user when prompted:

::

    cd project
    ./manage.py syncdb
    ./manage.py migrate mapit
    ./manage.py runserver

(Alternatively, set up a live web server however you wish - see the Deployment
Django documentation for details beyond the scope of this document.)

You can then visit http://localhost:8000/ and hopefully see the default MapIt homepage.
http://localhost:8000/admin/ should show the admin interface.

This is enough to have a working site. You can create areas and postcodes using the
admin interface and they will automatically work in the API-based front end.

However, if you have some bulk data you wish to import (which will make things
easier), you will need to import this data into MapIt. See the `country specific
READMEs`_ for instructions on their bulk imports, which should show the general
format for how it's done.


Country specific READMEs
------------------------

These are in the docs folder:

  * `UK <./docs/README-UK.rst>`_
  * `Norway <./docs/README-NORWAY.rst>`_

Improvements / patches
----------------------

Are welcome :)

ATB,
Matthew
