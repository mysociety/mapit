# mapit_make_fusion_csv.py
#
# This script is used to generate a CSV file with a column containing
# KML polygons for visualization with Google Fusion Tables.
#
# Copyright (c) 2011, 2012 UK Citizens Online Democracy. All rights reserved.
# Email: mark@mysociety.org; WWW: http://www.mysociety.org

# FIXME: add these instructions to code.fixmystreet.com as well

# Examples:
#
# In MapIt Global, find all countries:
#
#    ./manage.py mapit_make_fusion_csv --type=O02 --tolerance=0.001 global-countries.csv
#
# In MapIt Global, find all admin_level=10 areas in France:
#
#    ./manage.py mapit_make_fusion_csv --types=O10 --coveredby=28 france-10.csv
#
# (That assumes that 28 is the ID of the area corresponding to
# http://www.openstreetmap.org/browse/relation/1403916 in your MapIt.
# FIXME: it might be nice to be able to specify a relation or way ID
# instead of a MapIt Area ID here.)
#
# To import such CSV files into Google Fusion Tables, and make them
# look good, do the following:
#
#  1. Go to http://www.google.com/drive/start/apps.html#fusiontables
#  and click "Create a new table"
#
#  2. Select the CSV file you generated, with the defaults ("comma" as
#  the separator and UTF-8 encoding).  Then click "Next".
#
#  3. In the next dialog, the default ("Column names are in row 1")
#  should be fine, so just click "Next"
#
#  4. Put the correct attribution in the "Attribute data to" and the
#  "Attribution page link" fields (e.g. "OpenStreetMap contributors
#  and MapIt Global" and "http://global.mapit.mysociety.org/").  Then
#  click "Finish".

#  5. Now click on the "Map of name" tab.  Select "location" from the
#  "Tools -> Select location" submenu.

# 6. Go to "Tools -> Change map style ...", select Polygons -> Fill
# color, the Column tab, and specify the "color" column for colours.
#
# 7. You might need to switch to the "Rows 1" and back to the "Map of
# name" tab for the areas to be visible.
#
# 8. Go to File -> Share and change "Private" to "Anyone with the link"

from __future__ import print_function

import sys
import csv
from random import random, seed
import colorsys

from django.core.management.base import BaseCommand
from mapit.models import Area, Generation
from mapit.geometryserialiser import TransformError


def hsv_to_rgb(h, s, v):
    rgb = colorsys.hsv_to_rgb(h, s, v)
    return [int(x * 255) for x in rgb]


def rgb_for_html(r, g, b):
    return "%02x%02x%02x" % (r, g, b)


# From: http://stackoverflow.com/questions/3844801/check-if-all-elements-in-a-list-are-identical
def all_equal(iterator):
    try:
        iterator = iter(iterator)
        first = next(iterator)
        return all(first == rest for rest in iterator)
    except StopIteration:
        return True


class Command(BaseCommand):
    help = 'Generate a CSV file for Google Fusion Tables from MapIt'

    def add_arguments(self, parser):
        parser.add_argument(
            "--types", dest="types",
            help="The comma-separated types of the areas to return",
            metavar="TYPES")
        parser.add_argument(
            "--coveredby", dest="coveredby", type=int,
            help="Only include areas covered by AREA-ID",
            metavar="AREA-ID")
        parser.add_argument(
            "--generation", dest="generation",
            help="Specify the generation number", metavar="AREA-ID")
        parser.add_argument(
            "--tolerance", dest="tolerance", type=float, default=0.0001,
            help="Specify the simplifiy tolerance (default: 0.0001)", metavar="TOLERANCE")

    def handle(self, *args, **options):

        # To add a new query type, add it to this tuple, and add_arguments above:
        possible_query_types = ('coveredby',)

        if len(args) != 1:
            print("You must supply a CSV file name for output", file=sys.stderr)
            sys.exit(1)

        output_filename = args[0]

        if options['generation']:
            generation = Generation.objects.get(id=int(options['generation']))
        else:
            generation = Generation.objects.current()

        if not options['types']:
            print("Currently you must choose at least one type", file=sys.stderr)
            sys.exit(1)

        selected_query_types = [q for q in possible_query_types if options[q]]

        if not all_equal(options[q] for q in selected_query_types):
            print("The ID used in %s must be the same" % (", ".join(selected_query_types),), file=sys.stderr)
            sys.exit(1)

        if len(selected_query_types) > 0:
            area_id = options[selected_query_types[0]]
            areas = list(Area.objects.intersect(selected_query_types,
                                                Area.objects.get(id=area_id),
                                                options['types'].split(','),
                                                generation))

        else:
            areas = list(Area.objects.filter(type__code=options['types'],
                                             generation_low__lte=generation,
                                             generation_high__gte=generation))

        simplified_away = []
        empty_anyway = []

        with open(output_filename, "w") as fp:
            writer = csv.writer(fp)
            writer.writerow(["name", "color", "location"])
            for i, area in enumerate(areas):
                seed(area.name)
                hue = random()
                # line_rgb = rgb_for_html(*hsv_to_rgb(hue, 0.5, 0.5))
                fill_rgb = rgb_for_html(*hsv_to_rgb(hue, 0.5, 0.95))
                print("Exporting:", area)
                try:
                    kml, _ = area.export(4326,
                                         'kml',
                                         simplify_tolerance=options['tolerance'],
                                         kml_type="polygon")
                except TransformError:
                    simplified_away.append(area)
                    print("  (the area was simplified away to nothing)")
                    continue

                if kml is None:
                    empty_anyway.append(area)
                    print("  (the area was empty, skipping it)")
                    continue

                # The maximum cell size in Google Fusion tables is 1
                # million characters:
                #
                #   https://developers.google.com/fusiontables/docs/v1/using#geolimits
                #
                # (I'm assuming they really do mean characters, rather
                # than bytes after UTF-8 encoding.)

                if len(kml) > 1E6:
                    print("A cell for Google Fusion tables must be less than 1 million characters", file=sys.stderr)
                    print("but %s was %d characters" % (area, len(kml)), file=sys.stderr)
                    print("Try raising the simplify tolerance with --tolerance", file=sys.stderr)
                    sys.exit(1)

                writer.writerow([area.name.encode('utf-8') + " [%d]" % (area.id,),
                                 "#" + fill_rgb,
                                 kml.encode('utf-8')])

        if empty_anyway:
            print("The following areas had no polygons in the first place:")
            for area in empty_anyway:
                print("  ", area)

        if simplified_away:
            print("The following areas did have polygon data, but were simplified away to nothing:")
            for area in simplified_away:
                print("  ", area)
