# This script is used to export geometry information from Mapit
# as geojson (TODO: kml)
#
# Copyright (c) 2015 Openpolis. All rights reserved.
# Email: guglielmo at openpolis it; WWW: http://www.openpolis.it


import json
import logging
from optparse import make_option
from django.conf import settings
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.core.management.base import NoArgsCommand
import sys
from mapit.models import Area

__author__ = 'guglielmo'


class Command(NoArgsCommand):
    help = 'Export specified areas into a geojson file'
    option_list = NoArgsCommand.option_list + (
        make_option('--code-type',
                    dest='code_type',
                    help='Type of code to add as property in the geojson feature (ISTAT_COM, ...)'),
        make_option('--ids',
                    dest='ids',
                    default='',
                    help='Comma separated list of areas ids to export'),
        make_option('--filters',
                    dest='filters',
                    default='',
                    help='django_orm like filtering instructions (codes__code__contains:502&codes__code__lt:503'),
        make_option('--simplify-tolerance',
                    dest='simplify_tolerance',
                    default=0.,
                    help='Distance on the map within which more than 1 points will collapse.'),
        make_option('--srid',
                    dest='srid',
                    default='4326',
                    help='The SRID'),
        make_option('--outfile',
                    dest='outfile',
                    default=None,
                    help='Path to the output file (defaults to stdout)'),
    )

    FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    logger = logging.getLogger(__name__)

    def handle(self, **options):
        self.verbosity = options['verbosity']
        self.code_type = options['code_type']
        self.ids = options['ids']
        self.filters = options['filters']
        self.simplify_tolerance = float(options['simplify_tolerance'])
        self.srid = options['srid']
        self.outfile = options['outfile']

        # set log level, from verbosity
        if self.verbosity == '0':
            self.logger.setLevel(logging.ERROR)
        elif self.verbosity == '1':
            self.logger.setLevel(logging.WARNING)
        elif self.verbosity == '2':
            self.logger.setLevel(logging.INFO)
        elif self.verbosity == '3':
            self.logger.setLevel(logging.DEBUG)

        self.logger.info("Start")

        areas = Area.objects.select_related('type').all()

        if self.ids:
            self.ids = map(int, self.ids.split(','))
            areas = areas.filter(id__in=self.ids)

        self.logger.debug("Filters: {0}".format(self.filters))
        if self.filters:
            filters = dict(map(lambda x: x.split(":"), self.filters.split("&")))
            areas = areas.filter(**filters)

        # limit areas to 10 if no filters or ids are specified
        if not self.ids and not self.filters:
            areas = areas[:10]

        with (open(self.outfile, 'w') if self.outfile else sys.stdout) as out:
            out.write(
                self._areas_geojson(areas)
            )

        self.logger.info("End")

    def _areas_geojson(self, areas):
        out = {
            "type": "FeatureCollection",
            "features": []
        }
        for area in areas:
            self.logger.info(
                u"Processing {a.name} (id: {a.id})".format(a=area)
            )
            try:
                all_areas = area.polygons.all()
                if len(all_areas) > 1:
                    all_areas = all_areas.collect()
                elif len(all_areas) == 1:
                    all_areas = all_areas[0].polygon
                else:
                    return (None, None)

                if self.srid != settings.MAPIT_AREA_SRID:
                    all_areas.transform(self.srid)

                num_points_before_simplification = all_areas.num_points
                if self.simplify_tolerance:
                    n_removed_points = int(
                        num_points_before_simplification *
                        self.simplify_tolerance
                    )
                    all_areas = self.fix_geometry(
                        all_areas,
                        self.simplify_tolerance,
                        area.id, area.name
                    )
                    if all_areas.num_points == 0 and \
                       num_points_before_simplification > 0:
                        self.logger.warning(
                            u"Could not add this area." +
                            u"Zero points after simplification."
                        )
                        continue
                    else:
                        self.logger.debug(
                            u"  {0} points after simplification.".
                                format(all_areas.num_points)
                        )

            except Exception as e:
                self.logger.warning(
                    u"Could not add this area. " +
                    u"Exception {0}".format(e)
                )
                continue

            out['features'].append(
                {"type": "Feature",
                 "geometry": json.loads(all_areas.geojson),
                 "properties": {
                     "nome": area.name,
                     "codice": area.codes.get(
                         type__code=self.code_type
                     ).code if self.code_type else None
                 }
                }
            )
        return json.dumps(out)


    def fix_geometry(self, geom, precision, id, name):
        if type(geom).__name__ == 'Polygon':
            return self.fix_poly(geom, precision, id, name)
        if type(geom).__name__ == 'MultiPolygon':
            return self.fix_mpoly(geom, precision, id, name)


    def fix_poly(self, poly, precision, id, name):
        new_rings = []
        for ring in poly:
            points = ring.simplify(precision, preserve_topology=True)
            new_rings.append(points)
        new_poly = Polygon(*new_rings)
        return new_poly


    def fix_mpoly(self, mpoly, precision, id, name):
        new_polies = []
        for poly in mpoly:
            poly = self.fix_poly(poly, precision, id, name)
            new_polies.append(poly)
        new_mpoly = MultiPolygon(*new_polies)
        return new_mpoly


