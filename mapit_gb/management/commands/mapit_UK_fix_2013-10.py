# As per the comment in the 2013-10 control file, this script is to be run
# one-off after that import in order to get the four old boundaries back
# that were removed during that import.

from __future__ import print_function

import re

from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource
from django.utils import six

from mapit.models import Area, Code, CodeType, Type, Country, Generation, NameType
from mapit.management.command_utils import save_polygons


class Command(LabelCommand):
    help = 'Import OS Boundary-Line'
    args = '<May 2013 Boundary-Line unitary/district SHP file>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle_label(self, filename, **options):
        code_version = CodeType.objects.get(code='gss')
        name_type = NameType.objects.get(code='O')

        # Update the new areas to have the right codes
        # Northumberland, Gateshead, Stevenage, East Hertfordshire (in that order)
        areas_to_update = {
            2248: 'E06000057',
            2523: 'E08000037',
            2347: 'E07000243',
            2342: 'E07000242',
        }

        for id, code in areas_to_update.items():
            area = Area.objects.get(id=id)
            print("Updating: {0} to: {1}".format(area, code))
            area.generation_low = Generation.objects.new()
            if options['commit']:
                area.save()
            old_code = Code.objects.get(type__code='gss', area=area)
            old_code.code = code
            if options['commit']:
                old_code.save()

        # Add in new areas to represent the old boundaries too
        for feat in DataSource(filename)[0]:
            name = feat['NAME'].value
            if not isinstance(name, six.text_type):
                name = name.decode('iso-8859-1')
            name = re.sub('\s*\(DET( NO \d+|)\)\s*(?i)', '', name)
            name = re.sub('\s+', ' ', name)
            ons_code = feat['CODE'].value
            area_code = feat['AREA_CODE'].value
            country = ons_code[0]
            new_area = None
            # Gateshead, Stevenage, East Hertfordshire (in that order)
            if ons_code in ('E08000020', 'E07000101', 'E07000097'):
                new_area = self.make_new_area(name, ons_code, area_code, code_version, 1, 20, country)
            elif ons_code == 'E06000048':
                # Northumberland was only in the db from 11-20
                new_area = self.make_new_area(name, ons_code, area_code, code_version, 11, 20, country)
            if new_area and options['commit']:
                new_area.save()
                new_area.names.update_or_create(type=name_type, defaults={'name': name})
                new_area.codes.update_or_create(type=code_version, defaults={'code': ons_code})
                save_polygons({ons_code: (new_area, [feat.geom])})

    def make_new_area(self, name, ons_code, area_code, code_version, generation_low, generation_high, country):
        assert Area.objects.filter(codes__type=code_version, codes__code=ons_code).count() == 0
        print(ons_code, area_code, country, name)

        return Area(
            type=Type.objects.get(code=area_code),
            country=Country.objects.get(code=country),
            generation_low=Generation.objects.get(id=generation_low),
            generation_high=Generation.objects.get(id=generation_high),
        )
