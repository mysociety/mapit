# import_area_unions.py:
# This script is used to import regions (combinations of existing
# areas into a new area) into MaPit.
#
# Copyright (c) 2011 Petter Reinholdtsen.  Some rights reserved using
# the GPL.  Based on import_norway_osm.py by Matthew Somerville

import csv

from django.core.management.base import LabelCommand
from django.contrib.gis.geos import GEOSGeometry
from django.utils.six import Iterator

from mapit.models import Area, Generation, Geometry, Country, Type
from mapit.management.command_utils import save_polygons


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


class Command(LabelCommand):
    help = 'Import region data'
    args = '<CSV file listing name and which existing areas to combine into regions>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

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
                geometry = None
                for name in area_names.split(','):
                    name.strip()
                    name.lstrip()

                    try:
                        # Use this to allow '123 Name' in area definition
                        areaidnum = int(name.split()[0])
                        print("Looking up ID '%d'" % areaidnum)
                        args = {
                            'id__exact': areaidnum,
                            'generation_low__lte': current_generation,
                            'generation_high__gte': new_generation,
                            }
                    except (ValueError, IndexError):
                        print("Looking up name '%s'" % name)
                        args = {
                            'name__iexact': name,
                            'generation_low__lte': current_generation,
                            'generation_high__gte': new_generation,
                            }
                    area_id = Area.objects.filter(**args).only('id')
                    if 1 < len(area_id):
                        raise Exception("More than one Area named %s, use area ID as well" % name)
                    try:
                        print("ID: %d" % area_id[0].id)
                        args = {
                            'area__exact': area_id[0].id,
                            }
                        if geometry:
                            geometry = geometry | Geometry.objects.filter(**args)
                        else:
                            geometry = Geometry.objects.filter(**args)
                    except:
                        raise Exception("Area or geometry with name %s was not found!" % name)
                    unionoutline = geometry.unionagg()

                def update_or_create():
                    try:
                        m = Area.objects.get(id=int(regionid))
                        print("Updating area %s with id %d" % (regionname, int(regionid)))
                    except Area.DoesNotExist:
                        print("Creating new area %s with id %d" % (regionname, int(regionid)))
                        m = Area(
                            id=int(regionid),
                            name=regionname,
                            type=Type.objects.get(code=area_type),
                            country=Country.objects.get(code='O'),
                            generation_low=new_generation,
                            generation_high=new_generation,
                            )

                    if m.generation_high and current_generation \
                            and m.generation_high.id < current_generation.id:
                        raise Exception("Area %s found, but not in current generation %s" % (m, current_generation))
                    m.generation_high = new_generation

                    poly = [GEOSGeometry(unionoutline).ogr]
                    if options['commit']:
                        m.save()
                        save_polygons({regionid: (m, poly)})

                update_or_create()
            else:
                raise Exception("No area names found for region with name %s!" % regionname)
