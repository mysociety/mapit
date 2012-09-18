---
layout: default
title: How Data is Stored
---

How data is stored in MapIt
===========================

MapIt is designed to be very flexible and to be able to represent real world
situations. This means that geographic areas can have several names and
identifiers, and can change over time.

When you initially create a MapIt instance most of the complexity can be
ignored, but as you add and maintain the data you might need to take advantage
of it.

Areas
-----

`Area`s are the central part of MapIt. "California" is an area. The areas you
store depend on what you want to use MapIt for, but they'll most likely be
countries, states and other administrative boundaries.

It is possible for an area to have a parent and children, if you need to reflect a
hierarchy. So a 'county' can contain 'constituencies' and so on. Note that this
is different to one area covering another - it is only intended for defined
hierarchies. It is possible to search for overlapping, covering and touching
areas based only on their geometries.


Geometries
--------

An `Area` is actually made up of one or more `Geometries` - which define a
boundary. Most areas will be defined by a single geometry, but others may
require several. For example a country boundary may have a geometry for the
mainland, and then several smaller geometries for outlying islands. Geometries
are optional; you can store Areas with no associated geometry.


Area Types
---------

Each area has an associated type - this allows you to search just for states, or
local authorities. You'll create the area types before importing you data.

Each type has a name (eg 'Country') and a code (eg 'CTR'). You can choose both,
there is no set list.


Names
-----

An area can have several names, for example "United Kingdom", "United Kingdom of
Great Britain and Northern Ireland" and "UK" are all names for the same thing.
You could also add in "Royaume-Uni" which is the French.

Each name you add has a `NameType` - For the above examples you might use
'common', 'full', 'abbreviated' and 'french'.

To begin with you'll probably only use one `NameType`.


Codes
-----

As well as having names areas often have codes. For example the UK has the [ISO
3166 alpha 2](http://en.wikipedia.org/wiki/ISO_3166>) code `GB`. It is also
common for various bodies to assign codes.

To begin with you can ignore the codes, but like the names they'll probably come
in handy after a while.


Generations
-----------

Areas change over time, and by using `generations` you can store historic
areas for reference without having them appear in contemporary searches. You
can, if you want, specifically search particular generations.

For example say you have the boundaries of electoral areas - constituencies in
the UK. Between elections these are often adjusted to account for population
movements. You could store the 2007 boundaries in generation 1, the 2010
boundaries in generation 2 etc. If an area has not changed then it is in both
the generations.

There is a single `current` generation which is the one that is used by
default when searching - it is the most recent active one. It is also possible
to have `inactive` generations that don't appear in search results - this
allows you to add them to the system in advance but only activate them when
you're ready.

Postcodes
---------

Postcodes are named items, that optionally point to a location. In the UK we have
a large set of postcodes such as 'SW1A 1AA' that map to a latitude and longitude
(the centroid of all the addresses that use that postcode to be precise); but we
also hold postcodes of Crown Dependencies for which we do not know the location -
but we store them anyway, so we can at least say whether an entered postcode is
e.g. a valid Jersey postcode or not.

The Postcodes model could be used to store any sort of named points, not
necessarily postcodes or zip codes.


There is also a many-to-many table between Postcodes and Areas. This is for the
case where you have an Area without a geometry, but have some sort of list that
maps which postcodes are in which area. This is the case in the UK for Northern
Ireland Parliamentary constituencies, for example.

