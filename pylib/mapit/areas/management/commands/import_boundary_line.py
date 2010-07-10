from django.core.management.base import LabelCommand
# Not using LayerMapping as want more control, but what it does is what this does
#from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import *
from areas.models import Area

class Command(LabelCommand):
    def handle_label(self,  filename, **options):
        ds = DataSource(filename)
        layer = self.ds[0]
        for feat in layer:
            name = unicode(feat['NAME'], 'iso-8859-1')
            g = OGRGeometry(OGRGeomType('MultiPolygon'))
            g.add(feat.geom)

            ons_code = feat['CODE'] if feat['CODE'] != '999999' else None
            unit_id = feat['UNIT_ID']
            
            try:
                if ons_code:
                    m = Area.objects.get(codes__type='ons_code', codes__code=ons_code)
                elif unit_id:
                    m = Area.objects.get(codes__type='unit_id', codes__code=unit_id)
                else:
                    # UK Parliamentary Constituencies
                    # Need some way to decide whether to add new ones or not.
                    pass
            except Area.DoesNotExist:
                m = Area(
                    type = feat['AREA_CODE'],
                    polygon = g.wkt,
                )
                m.save()

            if not m.names.filter(type='O').update(name=name):
                m.names.create(type='O', name=name)
            if not m.codes.filter(type='ons_code').update(code=ons_code):
                m.codes.create(type='ons_code', code=ons_code)
            if not m.codes.filter(type='unit_id').update(code=unit_id):
                m.codes.create(type='unit_id', code=unit_id)

            # Increase/set generation numbers

