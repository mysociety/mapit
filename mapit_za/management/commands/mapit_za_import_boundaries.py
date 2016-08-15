# Create boundaries in MapIt for South Africa.  You need four
# shapefiles for these from:
#
#   http://www.demarcation.org.za/Downloads/Boundary/initial.html
#
# Example usage:
#
#   ./manage.py south_africa_import_boundaries \
#       --wards=south_africa/boundary-data/wards/Wards2011.shp \
#       --locals=south_africa/boundary-data/local-municipalities/LocalMunicipalities2011.shp \
#       --districts=south_africa/boundary-data/districts/DistrictMunicipalities2011.shp \
#       --provinces=south_africa/boundary-data/provinces/Province_New_SANeighbours.shp
#
# ... and then adding --commit if that looks OK.  Note that this
# doesn't check for invalid polygons yet, but there's an open pull
# request, one of whose commits would make it easy to add that:
#
#   https://github.com/mysociety/mapit/pull/73

import os
import re
import sys

from collections import namedtuple

from django.core.management import call_command
from django.core.management.base import BaseCommand

from mapit.models import Generation, NameType, Country


class Command(BaseCommand):
    """Import South African boundaries"""

    help = 'Import shapefiles with South African boundary data'

    def add_arguments(self, parser):
        parser.add_argument('--wards', '-w', help="The wards shapefile")
        parser.add_argument('--districts', '-d', help="The district municipalities shapefile")
        parser.add_argument('--provinces', '-p', help="The provinces shapefile")
        parser.add_argument('--locals', '-l', help="The local municipalities shapefile")
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle(self, **options):

        stop = False
        for k in ('wards',
                  'districts',
                  'provinces',
                  'locals'):
            if options[k]:
                if not os.path.exists(options[k]):
                    print >> sys.stderr, "The file %s didn't exist" % (options[k],)
                    stop = True
            else:
                print >> sys.stderr, "You must specify --" + re.sub(r'_', '-', k)
                stop = True
        if stop:
            sys.exit(1)

        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception("There's no inactive generation for the import")

        country = Country.objects.get(code='Z')

        name_type = NameType.objects.get(code='S')

        BoundaryType = namedtuple('BoundaryType',
                                  ['shapefile',
                                   'area_type_code',
                                   'code_field',
                                   'code_type_code',
                                   'name_field',
                                   'name_suffix_field'])

        boundary_types = [BoundaryType(shapefile=options['wards'],
                                       area_type_code='WRD',
                                       code_field='WARD_ID',
                                       code_type_code='w',
                                       name_field='MUNICNAME',
                                       name_suffix_field='WARDNO'),
                          BoundaryType(shapefile=options['locals'],
                                       area_type_code='LMN',
                                       code_field='CAT_B',
                                       code_type_code='l',
                                       name_field='MUNICNAME',
                                       name_suffix_field=None),
                          BoundaryType(shapefile=options['districts'],
                                       area_type_code='DMN',
                                       code_field='DISTRICT',
                                       code_type_code='d',
                                       name_field='MUNICNAME',
                                       name_suffix_field=None),
                          BoundaryType(shapefile=options['provinces'],
                                       area_type_code='PRV',
                                       code_field='CODE',
                                       code_type_code='p',
                                       name_field='PROVINCE',
                                       name_suffix_field=None)]

        standard_options = {
            'commit': options['commit']}

        for b in boundary_types:
            all_options = standard_options.copy()
            all_options.update({'generation_id': new_generation.id,
                                'area_type_code': b.area_type_code,
                                'name_type_code': name_type.code,
                                'country_code': country.code,
                                'code_field': b.code_field,
                                'code_type': b.code_type_code,
                                'name_field': b.name_field,
                                'name_suffix_field': b.name_suffix_field,
                                'new': False,
                                'use_code_as_id': False,
                                'encoding': 'ISO-8859-1'})
            call_command('mapit_import',
                         b.shapefile,
                         **all_options)
