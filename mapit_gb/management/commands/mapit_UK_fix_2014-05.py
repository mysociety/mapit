# This script is to be run as a one-off to fix up some geometries in the May
# 2014 edition of boundary line that are invalid.

from django.core.management.base import BaseCommand
from mapit.models import Area, CodeType
from mapit.management.command_utils import fix_invalid_geos_geometry


class Command(BaseCommand):
    help = 'Fix the UK boundary line import for May 2014'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle(self, **options):
        code_version = CodeType.objects.get(code='gss')

        # Get the polygons that we want to fix
        # The areas with bad polygons are:
        # E05009392 - LBW Colville
        # E05009400 - LBW Pembridge
        # W04000985 - CPC Pen Tranch Community
        # W04000980 - CPC Abersychan Community
        # W05000992 - UTE Abersychan
        # W05000999 - UTE Snatchwood

        areas_to_fix = (
            'E05009392',
            'E05009400',
            'W04000985',
            'W04000980',
            'W05000992',
            'W05000999',
        )

        for ons_code in areas_to_fix:
            area = Area.objects.get(codes__code=ons_code, codes__type=code_version)
            assert area.polygons.count() == 1
            area_polygon = area.polygons.all()[0]
            fixed_polygon = fix_invalid_geos_geometry(area_polygon.polygon)
            if fixed_polygon:
                print("Fixed polygon {0}".format(area_polygon))
                area_polygon.polygon = fixed_polygon
                if options['commit']:
                    area_polygon.save()
            else:
                print("Could not fix polygon {0}".format(area_polygon))
