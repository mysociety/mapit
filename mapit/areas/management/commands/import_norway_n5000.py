# import_norway_n5000.py:
# This script is used to import information from the N5000 datset available at
# http://www.statkart.no/nor/Land/Kart_og_produkter/N5000_-_gratis_oversiktskart/
#
# Copyright (c) 2011 UK Citizens Online Democracy. All rights reserved.
# Email: matthew@mysociety.org; WWW: http://www.mysociety.org

import re
import sys
from optparse import make_option
from django.core.management.base import LabelCommand
# Not using LayerMapping as want more control, but what it does is what this does
#from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import *
from mapit.areas.models import Area, Generation, Country, Type
from utils import save_polygons

class Command(LabelCommand):
    help = 'Import N5000 Kommunes'
    args = '<N5000_AdministrativFlate.shp file>'
    option_list = LabelCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle_label(self,  filename, **options):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception, "No new generation to be used for import!"

        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:
            name = unicode(feat['NAVN'].value, 'iso-8859-1')
            name = re.sub('\s+', ' ', name)
            print " ", name

            code = feat['KOMM'].value
            code_str = '%04d' % code
            area_code = 'NKO'
            
            try:
                m = Area.objects.get(codes__type='n5000', codes__code=code_str)
            except Area.DoesNotExist:
                m = Area(
                    id = code,
                    type = Type.objects.get(code=area_code),
                    country = Country.objects.get(code='O'),
                    generation_low = new_generation,
                    generation_high = new_generation,
                )

            if m.generation_high and current_generation and m.generation_high.id < current_generation.id:
                raise Exception, "Area %s found, but not in current generation %s" % (m, current_generation)
            m.generation_high = new_generation

            g = feat.geom.transform(4326, clone=True)
            poly = [ g ]

            if options['commit']:
                m.save()
                m.names.update_or_create({ 'type': 'M' }, { 'name': name })
                m.codes.update_or_create({ 'type': 'n5000' }, { 'code': code_str })
                save_polygons({ code : (m, poly) })

