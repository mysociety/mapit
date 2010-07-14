# This script is used to import information from OS Boundary-Line,
# which contains digital boundaries for administrative areas within
# Great Britain. Northern Ireland is handled separately, during the
# postcode import phase.

from django.core.management.base import LabelCommand
# Not using LayerMapping as want more control, but what it does is what this does
#from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import *
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
        for feat in layer:
            name = unicode(feat['NAME'].value, 'iso-8859-1')
            print "  ", name
            g = OGRGeometry(OGRGeomType('MultiPolygon'))
            g.add(feat.geom)

            ons_code = feat['CODE'] if feat['CODE'] != '999999' else None
            unit_id = feat['UNIT_ID']
            
            try:
                if ons_code:
                    m = Area.objects.get(codes__type='ons', codes__code=ons_code)
                elif unit_id:
                    m = Area.objects.get(codes__type='unit_id', codes__code=unit_id)
                else:
                    # UK Parliamentary Constituencies don't have any code in Boundary-Line
                    # (although they will have a code in GSS, looks like).
                    # Let us assume if there's one with the right name, we'll use that.
                    assert feat['AREA_CODE'] == 'WMC'
                    m = Area.objects.get(type=feat['AREA_CODE'], names__type='O', names__name=name)
            except Area.DoesNotExist:
                m = Area(
                    type = feat['AREA_CODE'],
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
                m.codes.update_or_create({ 'type': 'ons' }, { 'code': ons_code })
            if unit_id:
                m.codes.update_or_create({' type': 'unit_id' }, { 'code': unit_id })

