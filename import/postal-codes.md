---
layout: default
title: Importing postal codes
---

Importing postal codes
======================

If you have a CSV or TSV file of postal code data, you can load this into MapIt
directly. We'll assume you have installed MapIt as per the [installation
instructions](../install/) and that you have a CSV file containing postal codes
in the first column, latitude in the third column, and longitude in the fourth
column, and that it has a header row.

There is an import script that will look at the CSV file and create entries from
it. We'll call it as follows:

{% highlight bash %}
./manage.py mapit_import_postal_codes \
    --coord-field-lat 3 \
    --header-row        \
    /tmp/postal-codes.csv
{% endhighlight %}

That's all there is to it in this case, and it will update you on progress
every 1,000 imported postal codes.

Other options this import script have are:

* `--code-field N` -- The CSV column containing the postal code (defaults to 1)
* `--coord-field-lon N` -- The CSV column containing the longitude (or X)
  co-ordinate (defaults to latitude column + 1)
* `--no-location` -- Set if you don't have the location of the postal codes,
  only a list (still useful for checking validity of postal codes)
* `--srid` SRID -- Set to the SRID of the co-ordinates, if not WGS-84 (4326)
* `--strip` -- Set to strip spaces from the postal code before importing
* `--tabs` -- Set if the file uses tabs as a separator (TSV) rather than commas

So to import a TSV file, using the OSGB co-ordinate system (which uses eastings
and northings instead of longitude and latitude), with the easting in column 5,
the northing in column 7, and the postal code in column 10, with no header row,
you would do:

{% highlight bash %}
./manage.py mapit_import_postal_codes \
    --code-field 10     \
    --coord-field-lon 5 \
    --coord-field-lat 7 \
    --srid 27700        \
    --tabs              \
    /tmp/postal-codes.csv
{% endhighlight %}

Note:
If you get the error `django.db.utils.DatabaseError: invalid byte sequence for
encoding "UTF8": 0x00` at some point, you are probably being bitten by [this
bug](https://code.djangoproject.com/ticket/16778) - the solution is to add
`standard_conforming_strings = off` to your `postgresql.conf` file, or to apply
the patch in that ticket.

