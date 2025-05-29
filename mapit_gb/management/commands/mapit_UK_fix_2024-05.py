# This script is to be run as a one-off after an import of the May 2024 OS
# Boundary-Line in order to fix an issue with it. Until this edition, the two
# detached parts of CEDs Thorpe St Andrew and Lightwater, West End and Bisley
# had the same Unit IDs as their main parts, and we matched/joined on that. But
# this edition decided to change all the IDs and not even maintain this, so
# when we imported, both parts matched to the same Area and one polygon
# overwrote the other, leaving only one of the two in each CED. This script
# manually puts the correct geometries back in for these two areas.

import re
from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource

from mapit.models import Area
from mapit.management.command_utils import save_polygons

AREAS = ['Lightwater, West End and Bisley', 'Thorpe St Andrew']


def boundary_line_shapes(filename):
    for feat in DataSource(filename)[0]:
        name = feat['NAME'].value
        if not isinstance(name, str):
            name = name.decode('iso-8859-1')
        name = re.sub(r'\s*\(DET( NO \d+|)\)\s*(?i)', '', name)
        name = re.sub(r'\s+', ' ', name)
        name = name.replace('St.', 'St')
        name = name.replace(' ED', '')
        if name not in AREAS:
            continue
        feat.name = name
        yield feat


class Command(LabelCommand):
    help = 'Fix issues with May 2024 OS Boundary-Line'
    label = '<May 2024 Boundary-Line county electoral division SHP file>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle_label(self, filename, **options):
        geoms = {}
        for feat in boundary_line_shapes(filename):
            geoms.setdefault(feat.name, []).append(feat.geom)

        for name in AREAS:
            m = Area.objects.get(name=name, type__code='CED')
            print('Updating geometry of %s' % name)
            if options['commit']:
                save_polygons({"whatever": (m, geoms[name])})
