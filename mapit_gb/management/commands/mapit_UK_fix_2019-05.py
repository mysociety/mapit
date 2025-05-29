# This script is to be run as a one-off after an import of the original, buggy,
# May 2019 OS Boundary-Line, in order to fix the issues with it that are either
# fixed in the rerelease or remain unfixed until the next release.

from __future__ import print_function

import re
from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource

from mapit.models import Area, Code, CodeType, Type, Country, Generation, NameType
from mapit.management.command_utils import save_polygons


FIX_DIRECTLY = {
    'E05012199': 'E05012208',  # Sharoe Green
    'E0501239': 'E05012396',  # Darenth
}

FIX_WITH_OLD_BOUNDARY = {
    'E05002732': 'E05011571',  # Stretham
    'E05005276': 'E05012199',  # Garrison
    'E05005857': 'E05011847',  # Mundesley
    'E05005863': 'E05011853',  # Roughton
    'E05005865': 'E05011854',  # St Benet's
    'E05006336': 'E05012387',  # Seamer
    'E05009795': 'E05012630',  # Warwick Saltisford
    'E05010391': 'E05012990',  # Barton Ward (Canterbury)
    'E05010394': 'E05012991',  # Chartham & Stone Street Ward (Canterbury)
    'E05009767': 'E05012992',  # Kingston Bagpuize Ward (Vale of White Horse)
}


def boundary_line_shapes(filename):
    for feat in DataSource(filename)[0]:
        name = feat['NAME'].value
        if not isinstance(name, str):
            name = name.decode('iso-8859-1')
        name = re.sub(r'\s*\(DET( NO \d+|)\)\s*(?i)', '', name)
        name = re.sub(r'\s+', ' ', name)
        feat.name = name
        yield feat


class Command(LabelCommand):
    help = 'Fix issues with original May 2019 OS Boundary-Line'
    label = '<October 2018 Boundary-Line unitary/district SHP file>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle_label(self, filename, **options):
        code_version = CodeType.objects.get(code='gss')
        name_type = NameType.objects.get(code='O')

        # First, the easy ones
        for old, new in FIX_DIRECTLY.items():
            assert Area.objects.filter(codes__type=code_version, codes__code=new).count() == 0
            code = Code.objects.get(type=code_version, code=old)
            code.code = new
            print('Updating area %s to %s' % (old, new))
            if options['commit']:
                code.save()

        # Now, the harder ones
        previous_generation_low = {}
        previous_name = {}
        for old, new in FIX_WITH_OLD_BOUNDARY.items():
            if new != 'E05012199' or options['commit']:  # That one will exist unless it was updated above
                assert Area.objects.filter(codes__type=code_version, codes__code=new).count() == 0
            code = Code.objects.get(type=code_version, code=old)
            code.code = new
            previous_generation_low[old] = code.area.generation_low
            previous_name[old] = code.area.name
            code.area.generation_low = Generation.objects.current()
            print('Updating area %s to %s' % (old, new))
            if options['commit']:
                code.area.save()
                code.save()

        # Now we need to reinsert the October 2018 boundaries
        generation_high = Generation.objects.get(id=Generation.objects.current().id - 1)
        for feat in boundary_line_shapes(filename):
            ons_code = feat['CODE'].value
            if ons_code in FIX_WITH_OLD_BOUNDARY.keys():
                area_code = feat['AREA_CODE'].value
                country = Country.objects.get(code=ons_code[0])
                if options['commit']:  # They will be present if non-commit, they weren't changed above
                    assert Area.objects.filter(codes__type=code_version, codes__code=ons_code).count() == 0
                print('Creating new %s (%s), %s' % (ons_code, area_code, feat.name))

                m = Area(
                    type=Type.objects.get(code=area_code),
                    country=country,
                    generation_low=previous_generation_low[ons_code],
                    generation_high=generation_high,
                )
                if options['commit']:
                    m.save()
                    m.names.update_or_create(type=name_type, defaults={'name': feat.name})
                    m.codes.update_or_create(type=code_version, defaults={'code': ons_code})
                    save_polygons({ons_code: (m, [feat.geom])})
