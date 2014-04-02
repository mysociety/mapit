---
layout: page
title: Global (OpenStreetMap)
---

Global
======

MapIt Global contains boundaries extracted from OpenStreetMap.  In
order to create your own instance of MapIt Global you will need an
appreciable amount of free disk space - 500GB would be safe.  You
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

For this step, you should follow [instructions for setting up the
Overpass API server on the OpenStreetMap
wiki](wiki.openstreetmap.org/wiki/Overpass_API/install).  If you don't
want to update the database with daily diffs, then you can stop after
the "Static Usage" section.  If you do want to do daily updates, you
should also complete the "Applying minutely (or hourly, or daily)
diffs" section.  You don't need to set up the web service.

2 - Generating KML files
------------------------

Firstly, check that `osm3s_query` is in your `PATH`.  Then edit the
following line in `bin/boundaries.py` in your MapIt clone to point to
the Overpass database directory:

    osm3s_db_directory = "/home/overpass/db/"

The script to generate KML files caches the results of API queries in
`data/new-cache`, so if you've run the script on a previous occasion,
you may want to delete that with:

    rm -r data/new-cache/*

To generate the KML files, run the following script (possibly in a GNU
screen session, since this will take many hours):

    bin/get-boundaries-by-admin-level.py

That command will generate KML files in the
`data/cache-with-political/` subdirectory of your MapIt clone.

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
