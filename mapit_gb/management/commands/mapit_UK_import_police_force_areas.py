# This script is used to import police force area boundaries into MapIt. These
# boundaries are published as KML files at:
#
#     http://data.gov.uk/dataset/police-force-boundaries-england-and-wales
#
# The dataset also includes a very vague polygon for Northern Ireland with only
# 7 points - this will be imported, but you might want to delete it afterwards.
#
# Scotland is not covered by this dataset, but as of 1st April 2013 has one
# police force for the whole country, called Police Scotland.

from __future__ import print_function

import json
import os
import sys

from django.core.management import call_command
from django.core.management.base import LabelCommand
from django.utils.six.moves import urllib

from mapit.models import Type, NameType, Country, CodeType


DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')


class Command(LabelCommand):
    help = 'Import England, Wales and Northern Ireland police force area boundaries from .kml files'
    args = '<directory containing KML files from data.gov.uk>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'
        )
        parser.add_argument(
            '--generation_id',
            action="store",
            dest='generation_id',
            help='Which generation ID should be used',
        )
        parser.add_argument(
            '--area_type_code',
            action="store",
            dest='area_type_code',
            help='Which area type should be used (specify using code)',
        )
        parser.add_argument(
            '--name_type_code',
            action="store",
            dest='name_type_code',
            help='Which name type should be used (specify using code)',
        )
        parser.add_argument(
            '--code_type',
            action="store",
            dest='code_type',
            help='Which code type should be used (specify using its code)',
        )
        parser.add_argument(
            '--preserve',
            action="store_true",
            dest='preserve',
            help="Create a new area if the name's the same but polygons differ"
        )
        parser.add_argument(
            '--new',
            action="store_true",
            dest='new',
            help="Don't look for existing areas at all, just import everything as new areas"
        )
        parser.add_argument(
            '--fix_invalid_polygons',
            action="store_true",
            dest='fix_invalid_polygons',
            help="Try to fix any invalid polygons and multipolygons found"
        )

    def handle_label(self, directory, **options):

        err = False
        for k in ['generation_id', 'area_type_code', 'name_type_code', 'code_type']:
            if options[k]:
                continue
            print("Missing argument '--%s'" % k)
            err = True
        if err:
            sys.exit(1)

        generation_id = options['generation_id']
        area_type_code = options['area_type_code']
        name_type_code = options['name_type_code']
        code_type_code = options['code_type']

        try:
            Country.objects.get(code='E')
            Country.objects.get(code='W')
            Country.objects.get(code='N')
        except Country.DoesNotExist:
            print("England, Wales and Northern Ireland don't exist yet; load the UK fixture first.")
            sys.exit(1)
        welsh_forces = ('dyfed-powys', 'gwent', 'north-wales', 'south-wales')

        # The KML files don't contain the names of each force, but the filenames
        # are the force IDs used by the police API, so we can fetch the names
        # data and save the IDs as codes for future use:
        names_data_filename = os.path.join(DATA_DIRECTORY, "police_force_names.json")
        if not os.path.exists(names_data_filename):
            print(
                "Can't find force names data at %s; trying to fetch it from the police API instead..." %
                names_data_filename)
            url = "http://data.police.uk/api/forces"
            forces = urllib.request.urlopen(url)
            with open(names_data_filename, 'w') as f:
                f.write(forces.read())
            print("...successfully fetched and saved the force names data.")

        with open(names_data_filename) as names_file:
            names_data = json.load(names_file)

        # Map force codes to names for easy lookup:
        codes_to_names = dict((d['id'], d['name']) for d in names_data)

        # Ensure that these types exist already, because if --commit is not
        # specified then mapit_import will prompt for their descriptions
        # for each force:
        try:
            Type.objects.get(code=area_type_code)
            NameType.objects.get(code=name_type_code)
            CodeType.objects.get(code=code_type_code)
        except (Type.DoesNotExist, NameType.DoesNotExist, CodeType.DoesNotExist) as e:
            print(e, "Create the area, name and code types first.")
            sys.exit(1)

        print("Importing police force areas from %s" % directory)

        # mapit_import command kwargs which are common to all forces:
        command_kwargs = {
            'generation_id': generation_id,
            'area_type_code': area_type_code,
            'name_type_code': name_type_code,
            'code_type': code_type_code,
            'name_field': None,
            'code_field': None,
            'use_code_as_id': False,
            'encoding': None,
        }
        for option in ('commit', 'preserve', 'new', 'fix_invalid_polygons'):
            command_kwargs[option] = options[option]

        for kml_file in os.listdir(directory):
            code, extension = os.path.splitext(kml_file)
            if extension.lower() != '.kml':
                continue
            file_path = os.path.join(directory, kml_file)

            country_code = 'E'
            if code in welsh_forces:
                country_code = 'W'
            elif code == 'northern-ireland':
                country_code = 'N'

            try:
                name = codes_to_names[code]
            except KeyError:
                print("Could not find a force name in API JSON data for %s" % code)
                sys.exit(1)

            call_command(
                'mapit_import',
                file_path,
                override_name=name,
                override_code=code,
                country_code=country_code,
                **command_kwargs
            )
