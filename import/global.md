---
layout: page
title: Global (OpenStreetMap)
---

Global
======

MapIt Global contains boundaries extracted from OpenStreetMap.  In
order to create your own instance of MapIt Global you will need an
appreciable amount of free disk space - 100GB would be safe.  You
should also bear in mind that this is non-trivial to set up yourself -
if you're thinking of doing so, then you should strongly consider just
using [our live service](http://global.mapit.mysociety.org/).

There are three steps to creating an instance of MapIt Global:

1. Setting up your own Overpass API server, for efficient extraction of
   data from OpenStreetMap.

2. Generating a KML file for each closed boundary in OpenStreetMap

3. Importing the KML files into an instance of MapIt

If you set up the Overpass API to import daily diffs, then you only
need to do that step once, whereas the latter two would need to be run
whenever you want to create a new generation of data.

1 - Setting up your own Overpass API server
-------------------------------------------

For this step, you should follow [instructions for setting up the Overpass API
server on the OpenStreetMap
wiki](http://wiki.openstreetmap.org/wiki/Overpass_API/install), though note the
disc space saving below before populating the database. If you don't want to
update the database with daily diffs, then you can stop after the "Static
Usage" section. If you do want to do daily updates, you should also complete
the "Applying minutely (or hourly, or daily) diffs" section. You don't need to
set up the web service.

In order to save on disc space, we recommend that you use osmconvert and
osmfilter to filter out the required boundaries from the planet file before
importing them into Overpass. So after downloading a planet-latest.osm.bz2
file, you might want to run something like the following:

    bzcat planet-latest.osm.bz2 | osmconvert - --drop-author --out-o5m > planet.o5m
    osmfilter planet.o5m --drop-author --keep='boundary=administrative boundary=political' | bzip2 > planet-boundaries.osm.bz2

As of May 2014, the full planet file was 36G, as was the o5m file; the filtered
file was 757M. The Overpass database was then 15G.

2 - Generating KML files
------------------------

Firstly, check that `osm3s_query` is in your `PATH`. Then set the
`LOCAL_OVERPASS` configuration setting in `conf/general.yml` to True,
and the `OVERPASS_DB_DIRECTORY` to the location of your Overpass
database directory, e.g. `"/home/overpass/db/"`.

To generate the KML files, run the following script (possibly in a GNU
screen session, since this will take many hours):

    bin/get-boundaries-by-admin-level.py

You might need to run it with nice and ionice to be nice to others on your
server. The command will generate KML files in the
`data/cache-with-political/` subdirectory of your MapIt clone. In May 2014, the
KML output was 4.5G.

3 - Import the KML files into MapIt
----------------------------------

This step assumes that you have already set up an instance of MapIt,
[as described in the main installation instructions](/install/).

First, create some required types in MapIt by loading the `global`
fixture:

    ./manage.py loaddata global

You should then create a new generation into which we can import the
data:

    ./manage.py mapit_generation_create \
        --commit --desc "Initial import of MapIt Global data"

Then you can actually import the data with the following command.
(Again, this will take many hours to complete, so running it in GNU
screen would be a good move.)

    ./manage.py mapit_global_import \
        --verbosity 2 --commit ../data/cache-with-political/

Once that's completed successfully, you need to activate the
generation with:

    ./manage.py mapit_generation_activate --commit

If you're interested in more about how the boundaries are extracted
from OpenStreetMap, you may want to read these two blog posts:

* [Extracting Administrative Boundaries from OpenStreetMap – Part 1](http://diy.mysociety.org/2012/06/23/extracting-administrative-boundaries-from-openstreetmap/)
* [Extracting Boundaries from OpenStreetMap – Part 2](http://diy.mysociety.org/2012/12/04/extracting-boundaries-from-openstreetmap-part-2/)
