# As per the comment in the 2012-05 control file, this script is to be run
# one-off after that import in order to get the four old boundaries back
# that were removed during that import.

from __future__ import print_function

import re
from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource
from django.utils import six

from mapit.models import Area, CodeType, Type, Country, Generation, NameType
from utils import save_polygons


class Command(LabelCommand):
    help = 'Import OS Boundary-Line'
    args = '<October 2010 Boundary-Line unitary/district SHP file>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle_label(self, filename, **options):
        code_version = CodeType.objects.get(code='gss')
        name_type = NameType.objects.get(code='O')
        for feat in DataSource(filename)[0]:
            name = feat['NAME'].value
            if not isinstance(name, six.text_type):
                name = name.decode('iso-8859-1')
            name = re.sub('\s*\(DET( NO \d+|)\)\s*(?i)', '', name)
            name = re.sub('\s+', ' ', name)
            ons_code = feat['CODE'].value
            area_code = feat['AREA_CODE'].value
            country = ons_code[0]
            if ons_code in ('E07000100', 'E07000104', 'S12000009', 'S12000043'):
                assert Area.objects.filter(codes__type=code_version, codes__code=ons_code).count() == 0
                print(ons_code, area_code, country, name)

                m = Area(
                    type=Type.objects.get(code=area_code),
                    country=Country.objects.get(code=country),
                    generation_low=Generation.objects.get(id=1),
                    generation_high=Generation.objects.get(id=14),
                )
                if options['commit']:
                    m.save()
                    m.names.update_or_create(type=name_type, defaults={'name': name})
                    m.codes.update_or_create(type=code_version, defaults={'code': ons_code})
                    save_polygons({ons_code: (m, [feat.geom])})
