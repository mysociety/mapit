# import_area_unions.py:
# This script is used to import regions (combinations of existing
# areas into a new area) into MaPit.
#
# Copyright (c) 2011 Petter Reinholdtsen.  Some rights reserved using
# the GPL.  Based on import_norway_osm.py by Matthew Somerville

import csv
import sys
import re
from optparse import make_option
from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import *
from django.contrib.gis.geos import GEOSGeometry
from mapit.areas.models import Area, Generation, Geometry
from utils import save_polygons

# CVS format is
# ID;code;name;area1,area2,...;other;fields

# Copied from
# http://www.mfasold.net/blog/2010/02/python-recipe-read-csvtsv-textfiles-and-ignore-comment-lines/
class CommentedFile:
    def __init__(self, f, commentstring="#"):
        self.f = f
        self.commentstring = commentstring
    def next(self):
        line = self.f.next()
        while line.startswith(self.commentstring):
            line = self.f.next()
        return line
    def __iter__(self):
        return self

class Command(LabelCommand):
    help = 'Import region data'
    args = '<CSV file listing name and which existing areas to combine into regions>'
    option_list = LabelCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle_label(self, filename, **options):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            print "Using current generation %d" current_generation
            new_generation = current_generation
        else:
            print "Using new generation %d" new_generation

        print "Loading file %s" % filename
        region_line = csv.reader(CommentedFile(open(filename, "rb")),
                                 delimiter=';')

        for regionid, area_type, regionname, area_names, email, categories in region_line:
            print "Building region '%s'" % regionname
            if (-2147483648 > int(regionid) or 2147483647 < int(regionid)):
                print "Region ID %d is outside range of 32-bit integer" % regionid
                return 1 # FIXME Should return error and exit the import

            if area_names:
                # Look up areas using the names, find their geometry
                # and build a geometric union to set as the geometry
                # of the region.
                geometry = None
                for name in area_names.split(','):
                    name.strip()
                    name.lstrip()
                    print "Looking up name '%s'" % name

                    args = {
                        'name__iexact': name,
                        'generation_low__lte': current_generation,
                        'generation_high__gte': new_generation,
                        }
                    area_id = Area.objects.filter(**args).only('id')
                    try:
                        print "ID:", area_id[0].id
                        args = {
                            'area__exact': area_id[0].id,
                            }
                        if geometry:
                            geometry = geometry | Geometry.objects.filter(**args)
                        else:
                            geometry = Geometry.objects.filter(**args)
                    except:
                        print sys.exc_info()[0]
                        raise
#                        raise Exception, "Area with name %s was not found!" % name
                    unionoutline = geometry.unionagg()

                def update_or_create():
                    country = 'O' # Norway
                    try:
                        m = Area.objects.get(id=int(regionid))
                        print "Updating area %s with id %d" % (regionname, int(regionid))
                    except Area.DoesNotExist:
                        print "Creating new area %s with id %d" % (regionname, int(regionid))
                        m = Area(
                            id = int(regionid),
                            name = regionname,
                            type = area_type,
                            country = country,
                            generation_low = new_generation,
                            generation_high = new_generation,
                            )

                    if m.generation_high and current_generation \
                            and m.generation_high.id < current_generation.id:
                        raise Exception, "Area %s found, but not in current generation %s" % (m, current_generation)
                    m.generation_high = new_generation

                    poly = [ GEOSGeometry(unionoutline).ogr ]
                    if options['commit']:
                        m.save()
                        save_polygons({ regionid : (m, poly) })

                update_or_create()
            else:
                raise Exception, "No area names found for region with name %s!" % regionname
