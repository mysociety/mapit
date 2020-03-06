# This script is used after importing NI output areas to create the higher
# level boundaries for the existing areas.

from __future__ import print_function

from django.core.management.base import BaseCommand
from django.contrib.gis.db.models import Union
from mapit.models import Area, Type, Geometry


class Command(BaseCommand):
    help = 'Puts the boundaries on the LGDs, LGWs and LGEs from the Output Areas'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle(self, **options):
        area_type = Type.objects.get(code='OUA')
        done = []

        def save_polygons(area, **args):
            print('Working on', area.type.code, area.name, '...', end=' ')
            args['area__type'] = area_type
            geometry = Geometry.objects.filter(**args)
            p = geometry.aggregate(Union('polygon'))['polygon__union']
            if options['commit']:
                area.polygons.clear()
                if p.geom_type == 'Polygon':
                    shapes = [p]
                else:
                    shapes = p
                for g in shapes:
                    try:
                        existing = Geometry.objects.get(polygon__equals=g)
                        area.polygons.add(existing)
                    except Geometry.DoesNotExist:
                        area.polygons.create(polygon=g)
            done.append(area.id)
            print('done')

        for ward in Area.objects.filter(type=Type.objects.get(code='LGW')):
            save_polygons(ward, area__parent_area=ward)

            lge = ward.parent_area
            if lge.id not in done:
                save_polygons(lge, area__parent_area__parent_area=lge)

            council = lge.parent_area
            if council.id not in done:
                save_polygons(council, area__parent_area__parent_area__parent_area=council)
