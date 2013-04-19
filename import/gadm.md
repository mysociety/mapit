---
layout: default
title: Importing from GADM
---

Importing boundaries from GADM.org
==================================

[GADM](http://www.gadm.org/) is a database of administrative areas from
around the world. If you are setting up a MapIt for your country then it is
likely that this is a good starting point. At mySociety it is what we used for
Kenya and Nigeria.

Note that the GADM data is freely available for academic and other
non-commercial use. Redistribution, or commercial use, is not allowed without
prior permission from them.

These are step by step instructions for loading all the areas for a country
(we'll use Nigeria) into MapIt:

Find and download the boundaries
--------------------------------

1. Go to the download page: <http://www.gadm.org/country>
2. Select the country (in our case Nigeria)
3. Select the "Google Earth .kmz" format
4. Click "OK" to show the available downloads
5. Download all the "levels" to your computer -- for Nigeria there are levels 0,
   1 and 2.

\[ TODO: Talk about shapefile downloads here too -- some have more data than KML. \]

Preview the downloaded files
----------------------------

Once the data files have been downloaded you can use the free Google Earth
software to view the boundaries. It is available for download from:
http://www.google.com/earth/explore/products/desktop.html


Prepare the files for import
----------------------------

1. Collect all your files in one folder - we'll use `/tmp/gadm_data`
2. Convert the files to kml (kmz is just kml gzipped):

        cd /tmp/gadm_data
        # decompress all the kmz files
        unzip '*.kmz'


Work out the area types you'll need
-----------------------------------

There will be several different types of area you'll want to store. For example
there will be the country boundary, and there may also be states or counties.
Look in the kml files to find the different areas represented there.

This command will list them all:

    grep '<description>' *.kml | sort | uniq -c | grep -v 'href='

For the Nigerian kml files we get this output:

      1 NGA_adm0.kml:<description><![CDATA[NGA]]></description>
     37 NGA_adm1.kml:<description><![CDATA[State]]></description>
      1 NGA_adm1.kml:<description><![CDATA[Water body]]></description>
    775 NGA_adm2.kml:<description><![CDATA[Local Authority]]></descri...

The bit we're looking for is in the `CDATA[[...]]` block. The number at the
start of the line in the number of occurrences.

Note that there is a single 'Water Body' in one of the kml files - using a text
editor we'll remove that manually as it is not relevant to us. This is done by
finding the 'Water body' text and then deleting everything from and including
the `<Placemark>` before it and up to and including the closing `</Placemark>`
after it.

Alternatively you could import using the steps below and then find it in the
admin interface and delete it.


Prepare the MapIt install for the import
----------------------------------------

We'll assume that you are using a locally running instance of MapIt. If not
please change the URLs to match your setup.

1. Install MapIt as per the [installation instructions](../../install/).
2. Start the dev server.
3. We're assuming that your database is empty. If this is not the case you may 
   have some conflicts.
4. Either visit the admin at http://127.0.0.1:8000/admin and add a generation
   there, with description 'GADM version 2.0', or run the following (which does
   the same thing):

        ./manage.py mapit_generation_create \
            --desc='GADM version 2.0' --commit

5. (optional) You can add the various Types in the admin interface now, or be
   prompted for them when you run the import script. If you want to use the
   admin interface, we'll want a country - Nigeria with code N; a name type -
   'gadm' with description 'GADM English Name'; and appropriate area types, CTR
   "Country", STA "State", and LGA "Local Government Area".

Import the kml
--------------

There is an import script that will look at the kml file and create entries from
it. We'll call it as follows:

{% highlight bash %}
./manage.py mapit_import     \
    --country_code    N      \
    --generation_id   1      \
    --area_type_code  CTR    \
    --name_type_code  gadm   \
    --commit                 \
    /tmp/gadm_data/NGA_adm0.kml
{% endhighlight %}

You will be prompted to provide descriptions for the codes if you haven't
created them; we can use "GADM English Name" for gadm, "Country" for CTR,
"State" for STA, "Local Government Area" for LGA, and "Nigeria" for 'N'.

Repeat the above line for all your data files changing the path to the file and
the `--area_type_code` to suit your import. You may also need to use a
different value for `--generation_id` if this is not a fresh MapIt install.

If you want to try the import without committing to the database don't specify
the `--commit` switch.

(If you get the error `django.db.utils.DatabaseError: invalid byte sequence for
encoding "UTF8": 0x00` you are probably being bitten by [this
bug](https://code.djangoproject.com/ticket/16778) - the solution is to add
`standard_conforming_strings = off` to your `postgresql.conf` file, or to apply
the patch in that ticket.)

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

