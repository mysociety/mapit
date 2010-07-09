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
                area = Area.objects.get(codes__type='ons_code', codes__code=feat['CODE'])
                #area = Area.objects.get(codes__type='unit_id', codes__code=feat['UNIT_ID'])
            except Area.DoesNotExist:


                m = Area(
                    type = feat['AREA_CODE'],
                    polygon = g.wkt,
                )
                m.save()
                if not m.names.filter(type='O').update(name=feat['NAME']):
                    m.names.create(type='O', name=feat['NAME'])
                m.codes.filter(type='ons_code').update(code=feat['CODE'])
                m.codes.filter(type='unit_id').update(code=feat['UNIT_ID'])

        lm = LayerMapping(Area, filename, mapping, transform=False, encoding='iso-8859-1')
        lm.save(strict=True, verbose=True)

