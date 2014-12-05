---
layout: page
title: UK data
---

United Kingdom
==============

Here are the basic instructions to install OS OpenData and ONSPD:

1. AREA_SRID in conf/general.yml should be 27700 (as Boundary-Line shapes are
   in the OSGB projection).
2. Download the latest Code-Point Open, Boundary-Line and ONSPD from
   <http://parlvid.mysociety.org:81/os/>, and save/unzip in the data directory.
3. Change to the project directory, and create database tables (if you haven't
   already done this):

       ./manage.py syncdb
       ./manage.py migrate mapit

   Note if you had already done this but only then changed the AREA_SRID, you
   will need to `./manage.py migrate mapit zero` and then `./manage.py migrate
   mapit` again to get the right SRID in the database.

4. Run the following in order:

{% highlight bash %}
./manage.py mapit_generation_create --commit --desc "Initial import."
./manage.py loaddata uk
./manage.py mapit_UK_import_boundary_line \
    --control=mapit_gb.controls.first-gss --commit \
    `\ls ../data/Boundary-Line/Data/*.shp|\grep -v high_water`
# (You can run without --commit to do a dry run.)
# first-gss in the above assumes the Boundary Line you're importing
# is October 2010 or later, and uses the new GSS codes.
./manage.py mapit_UK_find_parents
./manage.py mapit_UK_import_codepoint ../data/Code-Point-Open/*.csv
./manage.py mapit_UK_scilly ../data/Code-Point-Open/tr.csv
./manage.py mapit_UK_import_nspd_ni_areas
./manage.py mapit_UK_import_nspd_ni ../data/ONSPD.csv
./manage.py mapit_UK_import_nspd_crown_dependencies ../data/ONSPD.csv
./manage.py mapit_generation_activate --commit
{% endhighlight %}

For notes on what was done to create generations as you can see on
<http://mapit.mysociety.org/>, see the end of this file.

Notes on future releases
------------------------

What to run when new data is released:

* Code-Point: mapit_UK_import_codepoint and mapit_UK_scilly
* ONSPD, no NI boundary changes: mapit_UK_import_nspd_ni
* ONSPD, NI boundary changes: mapit_UK_import_nspd_ni_areas then
  mapit_UK_import_nspd_ni (though note the first script is incomplete, it
  doesn't use a control file like mapit_UK_import_boundary_line does, as this
  has not yet been needed);
* Boundary-Line: Create a control file, mapit_UK_import_boundary_line and
  mapit_UK_find_parents.

You can manually increase the generation_high_id when something is new and
something else isn't (most commonly, a new Boundary-Line means a new generation
for Great Britain, and you can then increase the Northern Ireland boundaries
manually to be in the new generation).

Notes on creating what's live
-----------------------------

When creating what you see at mapit.mysociety.org, to enable it to have
pre-2010 election boundaries, I ran the above (or rather, what existed at the
time, which is not identical) twice, once with 2009-10 Boundary-Line and then
the 2010-05 edition. I had to write the 2010-05 control file you can see, did
not re-run mapit_UK_import_codepoint (as no postcodes had changed), and only
ran the NI stuff the second generation (as we only had current data). The
commands I basically ran are below.

Even worse, as I had to maintain IDs between our old and new versions of mapit,
I then matched up all IDs and names using the scripts in bin, manually inserted
some generation 10 areas (in data) for FixMyStreet and some generation 12 NI
WMC areas for WriteToThem, and manually added our test/fake areas that used to
be in code but can now happily sit in the database along with everything else.
You probably don't need any of that for your own install.

{% highlight bash %}
# Create inactive generation.
./manage.py mapit_UK_import_boundary_line \
    --control=mapit_gb.controls.2009-10 \
    `\ls ../../data/Boundary-Line/2009-10/*.shp|\grep -v high_water`
./manage.py mapit_UK_import_codepoint \
    ../../data/Code-Point-Open-2010-05/*.csv
./manage.py mapit_UK_find_parents
# Not importing NI here, as that only has the current boundaries.
./manage.py mapit_UK_scilly ../../data/Code-Point-Open-2010-05/tr.csv
# Make generation active, add another inactive generation
./manage.py mapit_UK_import_boundary_line \
    --control=mapit_gb.controls.2010-05 \
    `\ls ../../data/Boundary-Line/2010-05/*.shp|\grep -v high_water`
# mapit_UK_import_codepoint not needed as it's the same
# and there's no P-in-P tests!
./manage.py mapit_UK_find_parents
# I doubt the boundaries change! But updates the generation.
./manage.py mapit_UK_scilly ../../data/Code-Point-Open-2010-05/tr.csv
# This is now split into two scripts, see above.
./manage.py mapit_UK_import_nspd ../../data/NSPD-2010-05.csv
# Make generation active.
{% endhighlight %}

