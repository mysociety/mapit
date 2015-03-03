# import_area_unions.py:
# This script is used to import regions (combinations of existing
# areas into a new area) into MaPit.
#
# Copyright (c) 2011 Petter Reinholdtsen.  Some rights reserved using
# the GPL.  Based on import_norway_osm.py by Matthew Somerville

import csv
import logging
from optparse import make_option
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from django.core.management.base import LabelCommand
from django.contrib.gis.geos import GEOSGeometry
from django.db.models.query import EmptyQuerySet
from django.utils.six import Iterator

from mapit.models import Area, Generation, Geometry, Country, Type
from mapit.management.command_utils import save_polygons


# CSV format is
# ID;code;name;area1,area2,...

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
    option_list = LabelCommand.option_list + (
        make_option(
            '--commit', action='store_true', dest='commit', help='Actually update the database'
        ),
        make_option(
            '--country-code', dest='country_code', default='O', help='The country code to assign to created area'
        ),

    )

    FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    logger = logging.getLogger(__name__)

    def handle_label(self, filename, **options):
        self.verbosity = options['verbosity']

        # set log level, from verbosity
        if self.verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif self.verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif self.verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif self.verbosity == '3':
            self.logger.setLevel(logging.DEBUG)

        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            self.logger.info("Using current generation %d" % current_generation.id)
            new_generation = current_generation
        else:
            self.logger.info("Using new generation %d" % new_generation.id)

        self.logger.info("Loading file %s" % filename)
        region_line = csv.reader(CommentedFile(open(filename, "rb")),
                                 delimiter=';')

        for regionid, area_type, regionname, area_names in region_line:
            self.logger.info("Building region '%s'" % regionname)
            if regionid and regionid.trim() != "":
                regionid = int(regionid)
            else:
                regionid = 0

            if (-2147483648 > int(regionid) or 2147483647 < regionid):
                raise Exception("Region ID %d is outside range of 32-bit integer" % regionid)

            if area_names:
                # Look up areas using the names, find their geometry
                # and build a geometric union to set as the geometry
                # of the region.
                geometry = Geometry.objects.none()
                for name in area_names.split(','):
                    name.strip()
                    name.lstrip()

                    try:
                        # Use this to allow '123 Name' in area definition
                        areaidnum = int(name.split()[0])
                        self.logger.debug("Looking up ID '%d'" % areaidnum)
                        args = {
                            'id__exact': areaidnum,
                            'generation_low__lte': current_generation.id,
                            'generation_high__gte': new_generation.id,
                            }
                    except (ValueError, IndexError):
                        self.logger.debug("Looking up name '%s'" % name)
                        args = {
                            'name__iexact': name,
                            'generation_low__lte': current_generation.id,
                            'generation_high__gte': new_generation.id,
                            }

                    try:
                        area = Area.objects.get(**args)
                        self.logger.debug("ID: %d" % area.id)
                        args = {
                            'area__exact': area.id,
                            }
                    except Area.MultipleObjectsReturned:
                        raise Exception("More than one Area named %s, use area ID as well" % name)
                    except Area.DoesNotExist:
                        raise Exception("Area with name %s was not found!" % name)

                    geometry = geometry | Geometry.objects.filter(**args)


                unionoutline = geometry.unionagg()

                try:
                    m = Area.objects.get(id=regionid)
                    self.logger.info("Updating area %s with id %d" % (regionname, regionid))
                except Area.DoesNotExist:
                    m = Area(
                        name=regionname,
                        type=Type.objects.get(code=area_type),
                        country=Country.objects.get(code=options['country_code']),
                        generation_low=new_generation,
                        generation_high=new_generation,
                        )


                    # if id is explicitly specified
                    # then it is set
                    if regionid:
                        m.id = regionid

                    self.logger.info("Creating new area %s with id %d" % (regionname, int(regionid)))

                if m.generation_high and current_generation \
                        and m.generation_high.id < current_generation.id:
                    raise Exception("Area %s found, but not in current generation %s" % (m, current_generation))
                m.generation_high = new_generation

                poly = [GEOSGeometry(unionoutline).ogr]
                if options['commit']:
                    m.save()
                    save_polygons({regionid: (m, poly)})

            else:
                raise Exception("No area names found for region with name %s!" % regionname)
