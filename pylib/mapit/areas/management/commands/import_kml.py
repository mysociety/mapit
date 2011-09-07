# import_norway_osm.py:
# This script is used to import information from a KML file into MaPit.
#
# Copyright (c) 2011 UK Citizens Online Democracy. All rights reserved.
# Email: matthew@mysociety.org; WWW: http://www.mysociety.org

import re 
import xml.sax
from xml.sax.handler import ContentHandler
from optparse import make_option
from django.core.management.base import LabelCommand
# Not using LayerMapping as want more control, but what it does is what this does
#from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import *
from mapit.areas.models import Area, Generation
from utils import save_polygons

class Command(LabelCommand):
    help = 'Import KML data'
    args = '<KML files>'
    option_list = LabelCommand.option_list + (
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'
        ),
        make_option(
            '--generation_id',
            dest='generation_id',
            help='Which generation ID should be used',            
        ),
        make_option(
            '--country',
            dest='country',
            help='Which country should be used',            
        ),
        make_option(
            '--area_type',
            dest='area_type',
            help='Which area type should be used',            
        ),
        make_option(
            '--name_type',
            dest='name_type',
            help='Which name type should be used',            
        ),
    )

    def handle_label(self, filename, **options):

        print "Importing from %s" % filename

        generation = Generation.objects.get( id=options['generation_id'] )
        area_type  = options['area_type']
        name_type  = options['name_type']
        country    = options['country']

        # Need to parse the KML manually to get the ExtendedData
        kml_data = KML()
        xml.sax.parse(filename, kml_data)

        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:
            name = feat['Name'].value.decode('utf-8')
            name = re.sub('\s+', ' ', name)
            print "  looking at '%s'" % name.encode('utf-8')

            try:
                m = Area.objects.get(name=name, type=area_type)
            except Area.DoesNotExist:
                m = Area(
                    name            = name,
                    type            = area_type,
                    country         = country,
                    # parent_area     = parent_area,
                    generation_low  = generation,
                    generation_high = generation,
                )

            if m.generation_high != generation:
                raise Exception('generation has changed')
            
            # g = feat.geom.transform(4326, clone=True)
            g = feat.geom
            
            poly = [ g ]
            
            if options['commit']:
                m.save()
                m.names.update_or_create({ 'type': name_type }, { 'name': name })
                save_polygons({ m.id : (m, poly) })


class KML(ContentHandler):
    def __init__(self, *args, **kwargs):
        self.content = ''
        self.data = {}

    def characters(self, content):
        self.content += content

    def endElement(self, name):
        if name == 'name':
            self.current = {}
            self.data[self.content.strip()] = self.current
        elif name == 'value':
            self.current[self.name] = self.content.strip()
            self.name = None
        self.content = ''

    def startElement(self, name, attr):
        if name == 'Data':
            self.name = attr['name']

