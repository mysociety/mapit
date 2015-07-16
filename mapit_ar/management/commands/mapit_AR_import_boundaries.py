# Create boundaries in MapIt for South Africa.  You need four
# shapefiles for these from:
#
#   http://www.ign.gob.ar/NuestasActividades/sigign#descarga
#
# Example usage:
#
#   ./manage.py mapit_AR_import_boundaries \
#       --provincias=provincias/provincias.shp \
#       --departamentos=departamentos/departamentos.shp
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
from optparse import make_option

from django.core.management import call_command
from django.core.management.base import NoArgsCommand

from mapit.models import Generation, NameType, Country


class Command(NoArgsCommand):
    """Import South African boundaries"""

    help = 'Import shapefiles with South African boundary data'

    option_list = NoArgsCommand.option_list + (
        make_option(
            '--provincias', '-p',
            help="The provinces shapefile"),
        make_option(
            '--departamentos', '-d',
            help="The departments shapefile"),
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'),)

    def handle_noargs(self, **options):

        stop = False
        for k in ('provincias',
                  'departamentos'):
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

        country = Country.objects.get(code='A')

        name_type = NameType.objects.get(code='S')

        BoundaryType = namedtuple('BoundaryType',
                                  ['shapefile',
                                   'area_type_code',
                                   'code_field',
                                   'code_type',
                                   'name_field',
                                   'name_suffix_field'])

        boundary_types = [BoundaryType(shapefile=options['provincias'],
                                       area_type_code='PRV',
                                       code_field=None,
                                       code_type=None,
                                       name_field='nprov',
                                       name_suffix_field=None),
                          BoundaryType(shapefile=options['departamentos'],
                                       area_type_code='DPT',
                                       code_field='cod_depto',
                                       code_type='d',
                                       name_field='departa',
                                       name_suffix_field=None),
        ]

        standard_options = {
            'commit': options['commit']}

        for b in boundary_types:
            all_options = standard_options.copy()
            all_options.update({'generation_id': new_generation.id,
                                'area_type_code': b.area_type_code,
                                'name_type_code': name_type.code,
                                'country_code': country.code,
                                'name_field': b.name_field,
                                'new': False,
                                'use_code_as_id': False,
                                'encoding': 'ISO-8859-1'})
            if b.code_field:
                all_options.update({
                    'code_field': b.code_field,
                    'code_type': b.code_type,
                })
            call_command('mapit_import',
                         b.shapefile,
                         **all_options)
