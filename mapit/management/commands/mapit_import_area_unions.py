# import_area_unions.py:
# This script is used to import regions (combinations of existing
# areas into a new area) into MaPit.
#
# Copyright (c) 2011 Petter Reinholdtsen.  Some rights reserved using
# the GPL.  Based on import_norway_osm.py by Matthew Somerville

import csv
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models import Union
from django.utils.six import Iterator

from mapit.models import Area, Generation, Geometry, Country, Type
from mapit.management.command_utils import save_polygons
from mapit.management.commands.mapit_create_area_unions import Command


# CSV format is
# ID;code;name;area1,area2,...;email;categories

# Copied from
# http://www.mfasold.net/blog/2010/02/python-recipe-read-csvtsv-textfiles-and-ignore-comment-lines/
class CommentedFile(Iterator):
    def __init__(self, f, commentstring="#"):
        self.f = f
        self.commentstring = commentstring

    def __next__(self):
        line = next(self.f)
        while line.startswith(self.commentstring):
            line = next(self.f)
        return line

    def __iter__(self):
        return self


class Command(Command):
    help = 'Import region data'
    label = '<CSV file listing name and which existing areas to combine into regions>'
    country = Country.objects.get(code='O')

    def handle_label(self, filename, **options):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            print("Using current generation %d" % current_generation.id)
            new_generation = current_generation
        else:
            print("Using new generation %d" % new_generation.id)

        print("Loading file %s" % filename)
        region_line = csv.reader(CommentedFile(open(filename, "rb")),
                                 delimiter=';')

        for regionid, area_type, regionname, area_names, email, categories in region_line:
            print("Building region '%s'" % regionname)
            if (-2147483648 > int(regionid) or 2147483647 < int(regionid)):
                raise Exception("Region ID %d is outside range of 32-bit integer" % regionid)

            if area_names:
                # Look up areas using the names, find their geometry
                # and build a geometric union to set as the geometry
                # of the region.
                area_names.insert(0, regionid)
                area_names.insert(0, regionname)
                self.handle_row( area_names, {
                    'region-name': True,
                    'region-id': True,
                    'unionagg': True,
                    'commit': options['commit'],
                })

            else:
                raise Exception("No area names found for region with name %s!" % regionname)
