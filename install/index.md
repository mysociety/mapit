---
layout: page
title: Installing MapIt
---

Installation
============

There are several options for installing MapIt.  The rest of this page
describes how to do this manually, for people who are used to setting
up web applications, but there is also [an install script for Debian or Ubuntu servers](install-script) that may be easier.

If you prefer to set up each required component of MapIt yourself,
proceed with the instructions below.

General notes
-------------

MapIt currently uses Postgres/PostGIS as its database backend &ndash; there's no
reason  why e.g. SpatiaLite could not be used successfully, but it has never
been tried.

### 1. Installing GeoDjango/PostGIS

To install GeoDjango and PostGIS, please follow all the standard instructions
(including creating the template) over on the Django site at
[docs.djangoproject.com](http://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#ubuntudebian).
And anything else you need to set up Django as normal.

\[ Note for UK/Ireland: Not only is the PostGIS that is installed missing SRID
900913, as the GeoDjango docs tell you, but both SRID 27700 (British National
Grid) and SRID 29902 (Irish National Grid) can be incorrect (and they're quite
important for this application!). After you've installed and got a PostGIS
template, log in to it and update the proj4text column of SRID 27700 to include
+datum=OSGB36, and update SRID 29902 to have +datum=ire65. This may not be
necessary, depending on your version of PostGIS, but do check. \]

### 2. Installing other required packages

You will also need a couple of other packages, so install them:

    sudo apt-get install python-gdal


Installation as a Django app
----------------------------

As MapIt is a Django app, if you are making a GeoDjango project you can
use MapIt from within your project like any normal Django app:

* Install MapIt as a python package:

        pip install django-mapit
(or use -e git+https://github.com/mysociety/mapit to install from source control)
* Open your `settings.py` and edit as follows:
  * Add `mapit` and `django.contrib.gis` to your `INSTALLED_APPS`
  * Add `MAPIT_AREA_SRID` &ndash; the SRID of your area data (if in doubt, set to
    `4326`)
  * Add `MAPIT_COUNTRY` &ndash; used to supply country specific functions (such
    as postcode validation). If you look at the country files in
    `mapit/countries/` you can see how to add specialised
    country-specific functions.
  * Add `MAPIT_RATE_LIMIT` &ndash; a list of IP addresses or User Agents excluded
    from default rate limiting
* Set up the new database tables:
  * `./manage.py migrate`
* Add a line to your `urls.py` patterns pointing at `mapit.urls`, for example:

            (r'^mapit/', include('mapit.urls')),


Installation standalone with the example project
------------------------------------------------

* A standard git clone will get you the repository:

        git clone --recurse-submodules git://github.com/mysociety/mapit.git
        cd mapit

* Set up your configuration variables:

        cp conf/general.yml-example conf/general.yml

Now edit `conf/general.yml` to point to your local postgresql database, and
edit the other settings as per the documentation given in that file. If you
don't know what `AREA_SRID` to use, delete that line or set it to `4326`.
`COUNTRY` is optional and can be used for e.g. differing sorts of postcode
(zipcode) validation &ndash; if you look at the country files in
`mapit/countries/` you can see how to add specialised country-specific
functions to validate postcodes etc.

If you're going to be importing big datasets, make sure that `DEBUG` is
`False`; otherwise, you'll run out of memory as it tries to remember all the
SQL queries made during an import.

* Optionally, also turn off `escape_string_warning` in Postgres' config (unless
you want your server to run out of disc space logging all the errors, as ours
did the first time I imported overnight and didn't realise).

* At this stage, you should be able to set up the database and run the
development server. Firstly, set up a virtual environment and install the
required packages:

        virtualenv .venv
        source .venv/bin/activate
        pip install -e .

* Generate the CSS from the provided SASS:

        bin/mapit_make_css
        ./manage.py collectstatic

* Create the database tables:

        ./manage.py migrate mapit

* This can be a good time to add an admin user (though you can do this later):

        ./manage.py createsuperuser

* Run the development server

        ./manage.py runserver

(Alternatively, set up a live web server however you wish - see the Deployment
Django documentation for details beyond the scope of this document.)

You can then visit <http://localhost:8000/> and hopefully see the default MapIt
homepage. <http://localhost:8000/admin/> should show the admin interface.

This is enough to have a working site. You can create areas and postcodes using
the admin interface and they will automatically work in the API-based front
end.

However, if you have some bulk data you wish to import (which will make setup
easier), you will need to import this data into MapIt. Now see the section
on [importing data](../import/).
