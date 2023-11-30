---
layout: page
title: Importing UK boundary data
---

United Kingdom
==============

Here are the basic instructions to install UK data from OS OpenData, ONSPD, and OSNI Open Data:

1. AREA_SRID in conf/general.yml should be 27700 (as Boundary-Line shapes are
   in the OSGB projection).

2. Change to the project directory, and create database tables (if you haven't
   already done this):

        ./manage.py migrate

   Note if you had already done this but only then changed the AREA_SRID, you
   will need to `./manage.py migrate mapit zero` and then `./manage.py migrate
   mapit` again to get the right SRID in the database.

We use ONSPD to import all uk postcodes, Boundary-Line to import GB shapes, and OSNI to import NI shapes.  Code Point is not used.

1. Download the latest Boundary-Line, ONSPD, and OSNI data from
   <https://parlvid.mysociety.org/os/>, and save/unzip into a data directory.
   You need to unzip the OSNI data twice as it contains zipped folders.

2. Run the following in order (update any data paths as necessary):

{% highlight bash %}
./manage.py mapit_generation_create --commit --desc "Initial import."
./manage.py loaddata uk
./manage.py mapit_UK_import_boundary_line \
    --control=mapit_gb.controls.first-gss --commit \
    `\ls ../data/Boundary-Line/Data/GB/*.shp|\grep -v high_water`
./manage.py mapit_UK_import_osni --control=mapit_gb.controls.first-gss \
    --wmc=../data/OSNI/OSNI_Open_Data_Largescale_Boundaries__Parliamentary_Constituencies_2008/OSNI_Open_Data_Largescale_Boundaries__Parliamentary_Constituencies_2008.shp \
    --wmc-srid=4326 \
    --lgd=../data/OSNI/OSNI_Open_Data_Largescale_Boundaries__Local_Government_Districts_2012/OSNI_Open_Data_Largescale_Boundaries__Local_Government_Districts_2012.shp \
    --lgd-srid=4326 \
    --lge=../data/OSNI/OSNI_Open_Data_Largescale_Boundaries__District_Electoral_Areas_2012/OSNI_Open_Data_Largescale_Boundaries__District_Electoral_Areas_2012.shp \
    --lge-srid=29902 \
    --lgw=../data/OSNI/OSNI_Open_Data_Largescale_Boundaries_Wards_2012/OSNI_Open_Data_Largescale_Boundaries_Wards_2012.shp \
    --lgw-srid=4326 \
    --eur=../data/OSNI/OSNI_Open_Data_Largescale_Boundaries__NI_Outline/OSNI_Open_Data_Largescale_Boundaries__NI_Outline.shp \
    --eur-srid=29902 \
    --commit
./manage.py mapit_UK_add_names_to_ni_areas
./manage.py mapit_UK_find_parents --commit
./manage.py mapit_UK_import_onspd --crown-dependencies=include --northern-ireland=include ../data/ONSPD/Data/ONSPD_AUG_2016_UK.csv
./manage.py mapit_UK_scilly --commit
./manage.py loaddata uk_special_postcodes
./manage.py mapit_UK_add_ons_to_gss
./manage.py mapit_generation_activate --commit

{% endhighlight %}

Notes:

* All commands with a `--commit` argument can be run without that argument to
  do a dry run and see what would be imported
* Pay attention to the filenames used in the `mapit_UK_import_boundary_line`,
  `mapit_UK_import_osni` and `mapit_UK_import_onspd` commands.
  These are likely to change with newer releases so you'll have to
  change the command to refer to the correct filenames.
* Pay attention to the `--*-srid` options on the `mapit_UK_import_osni` command.
  This refers to the projection that the data was released in and it may change
  with new releases.  If the releases came from the mysociety cache you should find a `metadata.json` file in the OSNI folder that contains the SRID for
  each file.  If you obtained new releases yourself you can load the shapefiles
  in a tool such as [qgis](http://www.qgis.org/) to find the SRID yourself.
* Many of these commands take options that you may wish to investigate to
  customise the data imported to your database.

Notes on future releases
------------------------

What to run when new data is released:

* ONSPD: `mapit_UK_import_onspd`
* OSNI: Create a control file, `mapit_UK_import_osni` and `mapit_UK_find_parents`.
* Boundary-Line: Create a control file, `mapit_UK_import_boundary_line` and
  `mapit_UK_find_parents`.

You can manually increase the `generation_high_id` when something is new and
something else isn't.  For example a new Boundary-Line means a new generation
for Great Britain, and you can then increase the Northern Ireland boundaries
manually to be in the new generation and vice-versa for a new OSNI.
