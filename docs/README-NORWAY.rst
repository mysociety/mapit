Norway
======

Here are the basic instructions to install data from OSM:

1. Set AREA_SRID in conf/general.yml to 4326 (as OSM shapes are in WGS84).  
2. cd bin and run "python osm_to_kml" to fetch OSM XML and convert it to KML.
3. Change to the project directory, and create database tables:

::

   ./manage.py syncdb
   ./manage.py migrate mapit

4. Run the following (you can run anything without --commit to do a dry run):

::

   ./manage.py mapit_generation_create --commit --desc "Initial import."
   ./manage.py loaddata norway
   ./manage.py mapit_NO_import_osm --commit ../../data/cache/*.kml
   ./manage.py mapit_import_area_unions --commit data/norway/regions.csv
   ./manage.py mapit_generation_activate --commit

Please see below for information on where osm_to_kml gets its OSM data from.

Alternatively, here are the basic instructions to install the N5000 data:

1. Set AREA_SRID in conf/general.yml to 4326 (as we'll put N5000 shapes into
   the WGS84 co-ordinate system).
2. Download `N5000
   <http://www.statkart.no/nor/Land/Kart_og_produkter/N5000_-_gratis_oversiktskart/>`_
   and save/unzip in the data directory.
3. Change to the project directory, and create database tables:

::

   ./manage.py syncdb
   ./manage.py migrate mapit

4. Run the following (you can run anything without --commit to do a dry run):

::

   ./manage.py mapit_generation_create --commit --desc "Initial import."
   ./manage.py loaddata norway
   ./manage.py mapit_NO_import_n5000 --commit ../../data/N5000\ shape/N5000_AdministrativFlate.shp
   ./manage.py mapit_import_area_unions --commit data/norway/regions.csv
   ./manage.py mapit_generation_activate --commit

You should now be able to go to /point/4326/10.756389,59.949444 and have Oslo
returned as a result.

Norway OSM data
---------------

The way osm_to_kml works is to fetch a number of fixed and pre-defined relation
IDs from OSM - one (412437) containing all fylke, and then one for each fylke
containing all the kommune inside. These relations should stay and (now they're
correct) not change within OpenStreetmap, though of course the underlying
relations can have their boundaries improved and so on. See the relation_ids
list in the source of bin/osm_to_kml if you'd like to see the other relation
IDs.

The OSM tags 'name', and 'name:no' if 'name' is not set, are used to find the
primary name of the fylke and kommune. In addition, the values of the tags
'name:smi', 'name:fi' are imported into mapit. Only the primary name is shown
in the mapit web pages and JSON data, while the other names are stored in the
database.

The kommune and fylke number (ID) is fetched from a the tag 'ref' in OSM, and
if it is missing a static list of such IDS in mapit/data/norway/ids.csv is
consulted using the name (for fylke) or name+fylke (for kommune) as the key.
