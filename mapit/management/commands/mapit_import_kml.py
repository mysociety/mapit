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
from mapit.models import Area, Generation, Type, NameType, Country
from mapit.management.command_utils import save_polygons

from pprint import pprint

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
            action="store",
            dest='generation_id',
            help='Which generation ID should be used',            
        ),
        make_option(
            '--country_code',
            action="store",
            dest='country_code',
            help='Which country should be used',            
        ),
        make_option(
            '--area_type_code',
            action="store",
            dest='area_type_code',
            help='Which area type should be used (specify using code)',            
        ),
        make_option(
            '--name_type_code',
            action="store",
            dest='name_type_code',
            help='Which name type should be used (specify using code)',            
        ),
    )

    def handle_label(self, filename, **options):

        for k in ['generation_id','area_type_code','name_type_code','country_code']:
            if options[k]: continue
            raise Exception("Missing argument '--%s'" % k)

        generation_id  = options['generation_id']
        area_type_code = options['area_type_code']
        name_type_code = options['name_type_code']
        country_code   = options['country_code']

        area_type = Type.objects.get(code=area_type_code)
        name_type = NameType.objects.get(code=name_type_code)
        country   = Country.objects.get(code=country_code)

        print "Importing from %s" % filename
        
        if not options['commit']:
            print '(will not save to db as --commit not specified)'            

        current_generation = Generation.objects.current()
        new_generation     = Generation.objects.get( id=generation_id )

        # Need to parse the KML manually to get the ExtendedData
        kml_data = KML()
        xml.sax.parse(filename, kml_data)
        
        

        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:

            name = feat['Name'].value.decode('utf-8')
            name = re.sub('\s+', ' ', name)
            
            if not name:
                raise Exception( "Could not find a name to use for area" )
                
            print "  looking at '%s'" % name.encode('utf-8')

            try:
                m = Area.objects.get(name=name, type=area_type)
            except Area.DoesNotExist:
                m = Area(
                    name            = name,
                    type            = area_type,
                    country         = country,
                    # parent_area     = parent_area,
                    generation_low  = new_generation,
                    generation_high = new_generation,
                )

            # check that we are not about to skip a generation
            if m.generation_high and current_generation and m.generation_high.id < current_generation.id:
                raise Exception, "Area %s found, but not in current generation %s" % (m, current_generation)
            m.generation_high = new_generation
            
            g = feat.geom.transform(4326, clone=True)
            
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
