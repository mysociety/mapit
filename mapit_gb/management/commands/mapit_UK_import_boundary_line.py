# This script is used to import information from OS Boundary-Line,
# which contains digital boundaries for administrative areas within
# Great Britain. Northern Ireland is handled separately, during the
# postcode import phase.

import re
import sys

from django.core.management.base import LabelCommand
# Not using LayerMapping as want more control, but what it does is what this does
# from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource

from mapit.models import Area, Generation, Country, Type, CodeType, NameType, Code
from mapit.management.command_utils import save_polygons, fix_invalid_geos_geometry


class Command(LabelCommand):
    help = 'Import OS Boundary-Line'
    label = '<Boundary-Line SHP file>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--control', action='store', dest='control',
            help='Refer to a Python module that can tell us what has changed')
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    ons_code_to_shape = {}
    unit_id_to_shape = {}

    def handle_label(self, filename, **options):
        if not options['control']:
            raise Exception("You must specify a control file")
        __import__(options['control'])
        control = sys.modules[options['control']]

        code_version = CodeType.objects.get(code='gss')
        name_type = NameType.objects.get(code='O')
        code_type_os = CodeType.objects.get(code='unit_id')

        print(filename)
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception("No new generation to be used for import!")

        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:
            name = feat['NAME'].value or ''
            if not isinstance(name, str):
                name = name.decode('iso-8859-1')

            name = re.sub(r'\s*\(DET( NO \d+|)\)\s*(?i)', '', name)
            name = re.sub(r'\s+', ' ', name)

            ons_code = feat['CODE'].value if feat['CODE'].value not in ('999999', '999999999') else None
            unit_id = str(feat['UNIT_ID'].value)
            area_code = feat['AREA_CODE'].value
            patch = self.patch_boundary_line(name, ons_code, unit_id, area_code)
            if 'ons-code' in patch:
                ons_code = patch['ons-code']
            elif 'unit-id' in patch:
                unit_id = patch['unit-id']
            elif 'name' in patch:
                name = patch['name']

            if area_code == 'NCP':
                continue  # Ignore Non Parished Areas

            # The Senedd area codes were renamed in the May 2022 Boundary-Line.
            # Maintain the old codes for consistency.
            if area_code == 'WPC':
                area_code = 'WAC'
            if area_code == 'WPE':
                area_code = 'WAE'

            if ons_code in self.ons_code_to_shape:
                m, poly = self.ons_code_to_shape[ons_code]
                try:
                    m_name = m.names.get(type=name_type).name
                except ValueError:
                    m_name = m.name  # If running without commit for dry run, so nothing being stored in db
                if name != m_name:
                    raise Exception("ONS code %s is used for %s and %s" % (ons_code, name, m_name))
                # Otherwise, combine the two shapes for one area
                poly.append(feat.geom)
                continue

            if unit_id in self.unit_id_to_shape:
                m, poly = self.unit_id_to_shape[unit_id]
                try:
                    m_name = m.names.get(type=name_type).name
                except ValueError:
                    m_name = m.name  # If running without commit for dry run, so nothing being stored in db
                if name != m_name:
                    raise Exception("Unit ID code %s is used for %s and %s" % (unit_id, name, m_name))
                # Otherwise, combine the two shapes for one area
                poly.append(feat.geom)
                continue

            if ons_code:
                country = ons_code[0]  # Hooray!
            elif area_code in ('CED', 'CTY', 'DIW', 'DIS', 'MTW', 'MTD', 'LBW', 'LBO', 'LAC', 'GLA'):
                country = 'E'
            else:
                raise Exception(area_code)

            try:
                check = control.check(name, area_code, country, feat.geom, ons_code=ons_code, commit=options['commit'])
                if check is True:
                    raise Area.DoesNotExist
                if check == 'SKIP':
                    continue
                if isinstance(check, Area):
                    m = check
                    try:
                        ons_code = m.codes.get(type=code_version).code
                    except Code.DoesNotExist:
                        ons_code = None
                elif ons_code:
                    m = Area.objects.exclude(type__code='WMCF').get(codes__type=code_version, codes__code=ons_code)
                elif unit_id:
                    m = Area.objects.get(
                        codes__type=code_type_os, codes__code=unit_id, generation_high=current_generation)
                    m_name = m.names.get(type=name_type).name
                    if name != m_name:
                        raise Exception("Unit ID code %s is %s in DB but %s in SHP file" % (unit_id, m_name, name))
                else:
                    raise Exception('Area "%s" (%s) has neither ONS code nor unit ID' % (name, area_code))
                if int(options['verbosity']) > 1:
                    print("  Area matched, %s" % (m, ))
            except Area.DoesNotExist:
                print("  New area: %s %s %s %s" % (area_code, ons_code, unit_id, name))
                m = Area(
                    name=name,  # If committing, this will be overwritten by the m.names.update_or_create
                    type=Type.objects.get(code=area_code),
                    country=Country.objects.get(code=country),
                    generation_low=new_generation,
                    generation_high=new_generation,
                )

            if m.generation_high and current_generation and m.generation_high.id < current_generation.id:
                raise Exception("Area %s found, but not in current generation %s" % (m, current_generation))
            m.generation_high = new_generation
            if options['commit']:
                m.save()

            # Make a GEOS geometry only to check for validity:
            g = feat.geom
            geos_g = g.geos
            if not geos_g.valid:
                print("  Geometry of %s %s not valid" % (ons_code, m))
                geos_g = fix_invalid_geos_geometry(geos_g)
                if geos_g is None:
                    raise Exception("The geometry for area %s was invalid and couldn't be fixed" % name)
                    g = None
                else:
                    g = geos_g.ogr

            poly = [g]

            if options['commit']:
                m.names.update_or_create(type=name_type, defaults={'name': name})
            if ons_code:
                self.ons_code_to_shape[ons_code] = (m, poly)
                if options['commit']:
                    m.codes.update_or_create(type=code_version, defaults={'code': ons_code})
            if unit_id:
                self.unit_id_to_shape[unit_id] = (m, poly)
                if options['commit']:
                    m.codes.update_or_create(type=code_type_os, defaults={'code': unit_id})

        if options['commit']:
            save_polygons(self.unit_id_to_shape)
            save_polygons(self.ons_code_to_shape)

    def patch_boundary_line(self, name, ons_code, unit_id, area_code):
        """Used to fix mistakes in Boundary-Line. This patch function should
        return an ons-code key to replace the provided ONS code (and if None,
        match only on unit ID), or a unit-id key to replace the provided unit
        ID (and match only on ONS code if None).

        This function is here rather than the control file so that it will
        still be used on a first import."""
        if area_code == 'WMC' and ons_code == '42UH012':
            return {'ons-code': None}
        if area_code == 'UTA' and ons_code == 'S16000010':
            return {'ons-code': 'S12000010'}

        # Two incorrect IDs given in the October 2015 source
        if name == 'Badgers Mount CP' and area_code == 'CPC' and ons_code == 'E04012604':
            return {'ons-code': 'E04012605'}
        if name == 'Shoreham CP' and area_code == 'CPC' and ons_code == 'E04012605':
            return {'ons-code': 'E04012606'}

        # May 2016 has a duplicate unit ID
        if name == 'Coaley & Uley Ward' and area_code == 'DIW' and unit_id == '41867':
            return {'unit-id': None}

        # May 2019 has a duplicate unit ID
        if name == 'Northwich Leftwich Ward' and area_code == 'UTW' and unit_id == '174040':
            return {'unit-id': None}
        if name == 'Stour Valley Ward' and area_code == 'DIW' and unit_id == '174221':
            return {'unit-id': None}
        if name in ('Kirby-le-Soken & Hamford Ward', 'Thorpe, Beaumont & Great Holland Ward') and \
                area_code == 'DIW' and unit_id == '174247':
            return {'unit-id': None}

        # October 2019 gets Shetland Islands code wrong
        if area_code == 'WMC' and ons_code == 'S1400005':
            return {'ons-code': 'S14000051'}

        # May 2021 has two Abbey EDs - will need to check ID at next release
        if area_code == 'CED' and name == 'Abbey ED' and unit_id == '180320':
            return {'unit-id': '1290'}

        if area_code == 'UTW' and name == 'An Taobh Siar agus Nis Ward' and ons_code == 'S13003134':
            return {'ons-code': 'S13002608'}

        if area_code == 'DIW' and name == 'Loughton Fairmead Ward' and ons_code == 'E05015731':
            return {'ons-code': 'E05015730'}

        # Tewkesbury is *not* renaming, May 2025 has renamed it
        if name == 'North Gloucestershire District (B)' and ons_code == 'E07000083':
            return {'name': 'Tewkesbury District (B)'}

        return {}
