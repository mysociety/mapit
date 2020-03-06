# import_area_unions.py:
# This script is used to import regions (combinations of existing
# areas into a new area) into MaPit.
#
# Copyright (c) 2011 Petter Reinholdtsen.  Some rights reserved using
# the GPL.  Based on import_norway_osm.py by Matthew Somerville

import csv
from django.utils.six import Iterator
from mapit.models import Country
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
    option_defaults = { 'region-name-field': 1, 'region-id-field': 2, 'area-type-field': 3, 'unionagg': True }

    def process(self, filename, options):
        print("Loading file %s" % filename)
        region_line = csv.reader(CommentedFile(open(filename, "rb")),
                                 delimiter=';')

        for regionid, area_type, regionname, area_names, email, categories in region_line:
            print("Building region '%s'" % regionname)
            if (-2147483648 > int(regionid) or 2147483647 < int(regionid)):
                raise Exception("Region ID %d is outside range of 32-bit integer" % regionid)

            if not area_names:
                raise Exception("No area names found for region with name %s!" % regionname)

            row = [ regionname, regionid, area_type ]
            row.extend(area_names.split(','))
            self.handle_row( row, options )
