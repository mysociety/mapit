# This script is used to import information from OS Boundary-Line,
# which contains digital boundaries for administrative areas within
# Great Britain. Northern Ireland is handled separately, during the
# postcode import phase.

import re
import sys
from optparse import make_option
from django.core.management.base import LabelCommand
# Not using LayerMapping as want more control, but what it does is what this does
#from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import *
from mapit.areas.models import Area, Generation

class Command(LabelCommand):
    help = 'Import OS Boundary-Line'
    args = '<Boundary-Line SHP files (county before its wards, Euro before Westminster>'
    option_list = LabelCommand.option_list + (
        make_option('--control', action='store', dest='control', help='Refer to a Python module that can tell us what has changed'),
    )

    ons_code_to_shape = {}
    unit_id_to_shape = {}

    def handle_label(self,  filename, **options):
        if not options['control']:
            raise Exception, "You must specify a control file"
        __import__(options['control'])
        control = sys.modules[options['control']]

        print filename
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception, "No new generation to be used for import!"

        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:
            name = unicode(feat['NAME'].value, 'iso-8859-1')
            print " ", name

            name = re.sub('\s*\(DET( NO \d+|)\)\s*(?i)', '', name)
            #name = re.sub('\s*\(B\)$', '', name)

            ons_code = feat['CODE'].value if feat['CODE'].value != '999999' else None
            unit_id = str(feat['UNIT_ID'].value)
            area_code = feat['AREA_CODE'].value
            if self.patch_boundary_line(ons_code, area_code):
                ons_code = None
            
            if area_code == 'NCP': continue # Ignore Non Parished Areas

            if ons_code in self.ons_code_to_shape:
                m, poly = self.ons_code_to_shape[ons_code]
                m_name = m.names.get(type='O').name
                if name != m_name:
                    raise Exception, "ONS code %s is used for %s and %s" % (ons_code, name, m_name)
                # Otherwise, combine the two shapes for one area
                print "    Adding subsequent shape to ONS code %s" % ons_code
                poly.append(feat.geom)
                continue

            if unit_id in self.unit_id_to_shape:
                m, poly = self.unit_id_to_shape[unit_id]
                m_name = m.names.get(type='O').name
                if name != m_name:
                    raise Exception, "Unit ID code %s is used for %s and %s" % (unit_id, name, m_name)
                # Otherwise, combine the two shapes for one area
                print "    Adding subsequent shape to unit ID %s" % unit_id
                poly.append(feat.geom)
                continue

            if area_code in ('CED', 'CTY', 'DIW', 'DIS', 'MTW', 'MTD', 'LBW', 'LBO', 'LAC', 'GLA'):
                country = 'E'
            elif (area_code == 'EUR' and 'Scotland' in name) or area_code in ('SPC', 'SPE') or (ons_code and ons_code[0:3] in ('00Q', '00R')):
                country = 'S'
            elif (area_code == 'EUR' and 'Wales' in name) or area_code in ('WAC', 'WAE') or (ons_code and ons_code[0:3] in ('00N', '00P')):
                country = 'W'
            elif area_code in ('EUR', 'UTA', 'UTE', 'UTW', 'CPC'):
                country = 'E'
            else: # WMC
                # Euro regions should be loaded before Westminster...
                area_within = Area.objects.filter(type__in=('UTW','UTE','MTW','COP','LBW','DIW'), polygons__polygon__contained=feat.geom.geos)[0]
                country = area_within.country
            # Can't do the above ons_code checks with new GSS codes, will have to do more PinP checks
            # Do parents in separate P-in-P code after this is done.

            try:
                if control.check(name, area_code, country):
                    raise Area.DoesNotExist
                if ons_code:
                    m = Area.objects.get(codes__type='ons', codes__code=ons_code)
                elif unit_id:
                    m = Area.objects.get(codes__type='unit_id', codes__code=unit_id)
                    m_name = m.names.get(type='O').name
                    if name != m_name:
                        raise Exception, "Unit ID code %s is %s in DB but %s in SHP file" % (unit_id, m_name, name)
                else:
                    raise Exception, 'Area "%s" (%s) has neither ONS code nor unit ID' % (name, area_code)
            except Area.DoesNotExist:
                m = Area(
                    type = area_code,
                    country = country,
                    generation_low = new_generation,
                    generation_high = new_generation,
                )

            if m.generation_high and m.generation_high < current_generation:
                raise Exception, "Area %s found, but not in current generation %s" % (m, current_generation)
            m.generation_high = new_generation
            m.save()

            poly = [ feat.geom ]

            m.names.update_or_create({ 'type': 'O' }, { 'name': name })
            if ons_code:
                self.ons_code_to_shape[ons_code] = (m, poly)
                m.codes.update_or_create({ 'type': 'ons' }, { 'code': ons_code })
            if unit_id:
                self.unit_id_to_shape[unit_id] = (m, poly)
                m.codes.update_or_create({ 'type': 'unit_id' }, { 'code': unit_id })

        self.save_polygons(self.unit_id_to_shape)
        self.save_polygons(self.ons_code_to_shape)

    def patch_boundary_line(self, ons_code, area_code):
        """Fix mistakes in Boundary-Line"""
        if area_code == 'WMC' and ons_code == '42UH012':
            return True
        return False

    def save_polygons(self, lookup):
        for shape in lookup.values():
            m, poly = shape
            if not poly:
                continue
            sys.stdout.write(".")
            sys.stdout.flush()
            #g = OGRGeometry(OGRGeomType('MultiPolygon'))
            m.polygons.all().delete()
            for p in poly:
                if p.geom_name == 'POLYGON':
                    shapes = [ p ]
                else:
                    shapes = p
                for g in shapes:
                    m.polygons.create(polygon=g.wkt)
            #m.polygon = g.wkt
            #m.save()
            poly[:] = [] # Clear the polygon's list, so that if it has both an ons_code and unit_id, it's not processed twice
        print ""

