---
layout: default
title: Importing data
---

Importing data
==============

MapIt has two main sorts of data -- **boundary polygon data** (to show the
boundaries of councils or other types of administrative areas), and **postal
code point data** (if your country has a system of mapping strings to points in
some way, such as the UK postcode or the US zip code).

Once you have [installed the software](/install/), you could use its built-in
admin interface at `/admin/` to add types, generations, areas, and postal
codes, and they would work in the front end service. For details of the
different things you can add via the admin interface, see [how data is
stored](/how-data-is-stored/). You can draw and edit boundaries using the admin
editing function. If you have no digital boundaries or information, and this is
the only way to get data into your MapIt, then this would be the way to go.

However, if you have some bulk data you wish to import (such as KML files or
Shapefiles of boundary data, or CSV files of postal codes), you will probably
want to try and import this data into MapIt automatically.

If you have some KML or Shapefiles of some boundaries, you can load these into
MapIt directly using our import script -- see [Importing
boundaries](boundaries/) for more details.

Importing CSV-based postal code data is also straightforward -- see [Importing
postal codes](postal-codes/) for more details.

If you have other, more complicated, requirements, you might have to adapt or
write your own importer in Python -- you can see the current import scripts in
the `mapit/management/commands/` directory for how they work.

