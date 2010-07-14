# This script is used to import information from OS Boundary-Line,
# which contains digital boundaries for administrative areas within
# Great Britain. Northern Ireland is handled separately, during the
# postcode import phase.

import re
from django.core.management.base import LabelCommand
# Not using LayerMapping as want more control, but what it does is what this does
#from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import *
from django.contrib.gis.geos import MultiPolygon
from mapit.areas.models import Area, Generation

class Command(LabelCommand):
    help = 'Import OS Boundary-Line'
    args = '<Boundary-Line SHP files>'

    def handle_label(self,  filename, **options):
        print filename
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception, "No new generation to be used for import!"

        ds = DataSource(filename)
        layer = ds[0]
        ons_code_to_shape = {}
        unit_id_to_shape = {}
        for feat in layer:
            name = unicode(feat['NAME'].value, 'iso-8859-1')
            print " ", name

            name = re.sub('\s*\(DET( NO \d+|)\)\s*(?i)', '', name)
            #name = re.sub('\s*\(B\)$', '', name)

            ons_code = feat['CODE'].value if feat['CODE'].value != '999999' else None
            unit_id = str(feat['UNIT_ID'].value)
            area_code = feat['AREA_CODE'].value
            
            if area_code == 'NCP': continue # Ignore Non Parished Areas

            if ons_code in ons_code_to_shape:
                m = ons_code_to_shape[ons_code]
                m_name = m.names.get(type='O').name
                if name != m_name:
                    raise Exception, "ONS code %s is used for %s and %s" % (ons_code, name, m_name)
                # Otherwise, combine the two shapes for one area
                print "    Adding subsequent shape to ONS code %s" % ons_code
                new_poly = [ shape for shape in m.polygon ]
                new_poly.append(feat.geom.geos)
                m.polygon = MultiPolygon(new_poly)
                m.save()
                continue

            if unit_id in unit_id_to_shape:
                m = unit_id_to_shape[unit_id]
                m_name = m.names.get(type='O').name
                if name != m_name:
                    raise Exception, "Unit ID code %s is used for %s and %s" % (unit_id, name, m_name)
                # Otherwise, combine the two shapes for one area
                print "    Adding subsequent shape to unit ID %s" % unit_id
                new_poly = [ shape for shape in m.polygon ]
                new_poly.append(feat.geom.geos)
                m.polygon = MultiPolygon(new_poly)
                m.save()
                continue

            try:
                if ons_code:
                    m = Area.objects.get(codes__type='ons', codes__code=ons_code)
                elif unit_id:
                    m = Area.objects.get(codes__type='unit_id', codes__code=unit_id)
                else:
                    # UK Parliamentary Constituencies don't have any code in Boundary-Line
                    # (although they will have a code in GSS, looks like).
                    # Let us assume if there's one with the right name, we'll use that.
                    assert area_code == 'WMC'
                    m = Area.objects.get(type=area_code, names__type='O', names__name=name)
            except Area.DoesNotExist:
                g = OGRGeometry(OGRGeomType('MultiPolygon'))
                g.add(feat.geom)
                country = ''
                if area_code in ('CED', 'CTY', 'DIW', 'DIS', 'MTW', 'MTD', 'LBW', 'LBO', 'LAC', 'GLA'):
                    country = 'E'
                elif (area_code == 'EUR' and 'Scotland' in name) or area_code in ('SPC', 'SPE') or (ons_code and ons_code[0:3] in ('00Q', '00R')):
                    country = 'S'
                elif (area_code == 'EUR' and 'Wales' in name) or area_code in ('WAC', 'WAE') or (ons_code and ons_code[0:3] in ('00N', '00P')):
                    country = 'W'
                elif area_code in ('EUR', 'UTA', 'UTE', 'UTW', 'CPC'):
                    country = 'E'
                # That leaves WMC
                # Can't do the above ons_code checks with new GSS codes, will have to do more PinP checks
                # Do parents and WMC countries in separate PinP code after this is done.
                m = Area(
                    type = area_code,
                    country = country,
                    polygon = g.wkt,
                    generation_low = new_generation,
                    generation_high = new_generation,
                )
                m.save()

            if m.generation_high and m.generation_high < current_generation:
                raise Exception, "Area %s found, but not in current generation %s" % (m, current_generation)
            m.generation_high = new_generation
            m.save()

            m.names.update_or_create({ 'type': 'O' }, { 'name': name })
            if ons_code:
                ons_code_to_shape[ons_code] = m
                m.codes.update_or_create({ 'type': 'ons' }, { 'code': ons_code })
            if unit_id:
                unit_id_to_shape[unit_id] = m
                m.codes.update_or_create({ 'type': 'unit_id' }, { 'code': unit_id })

