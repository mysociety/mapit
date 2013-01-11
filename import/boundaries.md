---
layout: default
title: Importing boundary data
---

Importing boundary data
=======================

If you have some KML or Shapefiles of some boundaries, you can load these into
MapIt directly. The import script is used to import boundaries of a certain
'type' at once (for example, all county councils, or all kommunes), which is
generally how boundary data is distributed.

We'll assume that you are using a locally running instance of MapIt. If not
please change the URLs to match your setup. For the below, let us assume you
are in France, and you are importing boundary data of arrondissements
(districts) from a source called 'BoundaryInfo'.

(If you get the error `django.db.utils.DatabaseError: invalid byte sequence for
encoding "UTF8": 0x00` at some point, you are probably being bitten by [this
bug](https://code.djangoproject.com/ticket/16778) - the solution is to add
`standard_conforming_strings = off` to your `postgresql.conf` file, or to apply
the patch in that ticket.)

Set things up
-------------

1. Install MapIt as per the [installation instructions](../install/).
2. Start the dev server.
3. We're assuming that your database is empty. If this is not the case you may 
   have some conflicts.
4. Either visit the admin at http://127.0.0.1:8000/admin and add a generation
   there, with description 'Initial import', or run the following (which does
   the same thing):

        ./manage.py mapit_generation_create --desc='Initial import' --commit

   Generations are so you can load in boundary data that changes over time --
   you can import new versions of boundaries without them being actually 'live'
   until they're ready, and leave old versions available for people to use for
   historical research.

5. (optional) You can add the various Types in the admin interface now, or be
   prompted for them when you run the import script. If you want to use the
   admin interface, we'll want a country France, with a one letter code F (MapIt
   codes are as they are for bad historical reasons; you probably won't need to
   use this country code); a name type (as you can have multiple names),
   describing the source of this name (so perhaps 'binfo' with description
   'BoundaryInfo'); and an appropriate area type, such as ARR
   "Arrondissements" (again, the limitation on the area type is historical,
   apologies).

Import the kml
--------------

There is an import script that will look at the KML file and create entries from
it. We'll call it as follows:

{% highlight bash %}
./manage.py mapit_import     \
    --country_code    F      \
    --generation_id   1      \
    --area_type_code  ARR    \
    --name_type_code  binfo  \
    --commit                 \
    /tmp/data/ArrondissementsData.kml
{% endhighlight %}

You will be prompted to provide descriptions for the codes if you haven't
created them; we can use "BoundaryInfo" for binfo, "Arrondissements" for ARR,
and "France" for 'F'.

You can repeat the above line for different data files, changing the path to
the file and the `--area_type_code` to suit your import. You may also need to
use a different value for `--generation_id` if this is not a fresh MapIt
install.

If you want to try the import without committing to the database don't specify
the `--commit` switch.

Activate the generation
-----------------------

Once you are happy that the data is correct activate the generation in the
admin interface, or run:

    ./manage.py mapit_generation_activate --commit


Shapefiles
----------

The same import script can import shapefiles too. You might need the extra
command line parameter of `--encoding` if the encoding of the shapefile is not
UTF-8 (GADM is sometimes ISO-8859-1, for example).

You will also need to know which field in the shapefile contains the name of
the area, and specify it with the `--name_field` parameter. If you run without
this parameter and 'Name' doesn't work, the program will output a list of
possible choices that it could be.

GeoJSON
-------

That import command (`./manage.py mapit_import ...`) also works for
importing GeoJSON files.  As with shapefiles, you may have to specify
the key that corresponds to the name of the area by using the
`--name_field` parameter.  If you run without this parameter and
'Name' doesn't work, the program will output a list of possible
choices that it could be.

Areas with IDs
--------------

If your Shapefile contains a key containing a code associated with each area,
then the import script can include that. The associated command line arguments
are:

* `--code_field` -- as with `--name_field`, this specifies the field in the
  shapefile containing the code. The script will list possible choices if it
  can't find the one you provide.
* `--code_type` -- the code for the type of ID this is (e.g. if it was the
  Ordnance Survey's ID for this area, we could use 'OS' here).

