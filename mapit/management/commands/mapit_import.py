# This script is used to import geometry information, from a shapefile or KML
# file, into MapIt.
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
from mapit.models import Area, Generation, Type, NameType, Country, CodeType
from mapit.management.command_utils import save_polygons

class Command(LabelCommand):
    help = 'Import geometry data from .shp or .kml files'
    args = '<SHP/KML files>'
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
        make_option(
            '--code_type',
            action="store",
            dest='code_type',
            help='Which code type should be used (specify using its code)',
        ),
        make_option(
            '--name_field',
            action="store",
            dest='name_field',
            help="The field name containing the area's name"
        ),
        make_option(
            '--code_field',
            action="store",
            dest='code_field',
            help="The field name containing the area's ID code"
        ),
        make_option(
            '--encoding',
            action="store",
            dest='encoding',
            help="The encoding of names in this dataset"
        ),
    )

    def handle_label(self, filename, **options):

        err = False
        for k in ['generation_id','area_type_code','name_type_code','country_code']:
            if options[k]: continue
            print "Missing argument '--%s'" % k
            err = True
        if err:
            sys.exit(1)

        generation_id = options['generation_id']
        area_type_code = options['area_type_code']
        name_type_code = options['name_type_code']
        country_code = options['country_code']
        name_field = options['name_field'] or 'Name'
        code_field = options['code_field']
        code_type_code = options['code_type']
        encoding = options['encoding'] or 'utf-8'

        if len(area_type_code)>3:
            print "Area type code must be 3 letters or fewer, sorry"
            sys.exit(1)

        if (code_field and not code_type_code) or (not code_field and code_type_code):
            print "You must specify both code_field and code_type, or neither."
            sys.exit(1)
        try:
            area_type = Type.objects.get(code=area_type_code)
        except:
            type_desc = raw_input('Please give a description for area type code %s: ' % area_type_code)
            area_type = Type(code=area_type_code, description=type_desc)
            if options['commit']: area_type.save()

        try:
            name_type = NameType.objects.get(code=name_type_code)
        except:
            name_desc = raw_input('Please give a description for name type code %s: ' % name_type_code)
            name_type = NameType(code=name_type_code, description=name_desc)
            if options['commit']: name_type.save()

        try:
            country = Country.objects.get(code=country_code)
        except:
            country_name = raw_input('Please give the name for country code %s: ' % country_code)
            country = Country(code=country_code, name=country_name)
            if options['commit']: country.save()

        if code_type_code:
            try:
                code_type = CodeType.objects.get(code=code_type_code)
            except:
                code_desc = raw_input('Please give a description for code type %s: ' % code_type_code)
                code_type = CodeType(code=code_type_code, description=code_desc)
                if options['commit']: code_type.save()

        print "Importing from %s" % filename

        if not options['commit']:
            print '(will not save to db as --commit not specified)'

        current_generation = Generation.objects.current()
        new_generation     = Generation.objects.get( id=generation_id )

        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:

            try:
                name = feat[name_field].value
            except:
                choices = ', '.join(layer.fields)
                print "Could not find name using name field '%s' - should it be something else? It will be one of these: %s. Specify which with --name_field" % (name_field, choices)
                sys.exit(1)
            try:
                name = name.decode(encoding)
            except:
                print "Could not decode name using encoding '%s' - is it in another encoding? Specify one with --encoding" % encoding
                sys.exit(1)

            name = re.sub('\s+', ' ', name)
            if not name:
                raise Exception( "Could not find a name to use for area" )

            code = None
            if code_field:
                try:
                    code = feat[code_field].value
                except:
                    choices = ', '.join(layer.fields)
                    print "Could not find code using code field '%s' - should it be something else? It will be one of these: %s. Specify which with --code_field" % (code_field, choices)
                    sys.exit(1)

            print "  looking at '%s'%s" % ( name.encode('utf-8'), (' (%s)' % code) if code else '' )

            try:
                if code:
                    m = Area.objects.get(codes__code=code, codes__type=code_type)
                else:
                    # Assumes unique names if no code column used
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
                if code:
                    m.codes.update_or_create({ 'type': code_type }, { 'code': code })
                save_polygons({ m.id : (m, poly) })

