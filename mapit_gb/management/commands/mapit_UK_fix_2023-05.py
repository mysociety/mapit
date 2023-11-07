# This script is to be run as a one-off after an import of the May 2023 OS
# Boundary-Line in order to fix an issue with it

import re
from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource

from mapit.models import Area, Code, CodeType, Type, Country, Generation, NameType
from mapit.management.command_utils import save_polygons


FIX_WITH_OLD_BOUNDARY = {
    'E05012751': 'E05015549',  # Martlesham & Purdis Farm Ward (East Suffolk)
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
    help = 'Fix issues with May 2023 OS Boundary-Line'
    label = '<October 2022 Boundary-Line unitary/district ward SHP file>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle_label(self, filename, **options):
        code_version = CodeType.objects.get(code='gss')
        name_type = NameType.objects.get(code='O')

        previous_generation_low = {}
        previous_name = {}
        for old, new in FIX_WITH_OLD_BOUNDARY.items():
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

        # Now we need to reinsert the October 2022 boundaries
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
