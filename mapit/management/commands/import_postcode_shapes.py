# import_global_osm.py:
#
# This script is used to import administrative boundaries from
# OpenStreetMap into MaPit.
#
# It takes KML data generated either by
# get-boundaries-by-admin-level.py or get-boundaries-from-planet.py
# so you need to have run one of those first.
#
# This script is heavily based on import_norway_osm.py by Matthew
# Somerville.
#
# Copyright (c) 2011, 2012 UK Citizens Online Democracy. All rights reserved.
# Email: mark@mysociety.org; WWW: http://www.mysociety.org

import os
import re
import xml.sax
from xml.sax.handler import ContentHandler
from optparse import make_option
from django.core.management.base import LabelCommand
# Not using LayerMapping as want more control, but what it does is what this does
#from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import *
from mapit.models import Area, Generation, Country, Type, Code, CodeType, NameType
from utils import save_polygons
from glob import glob
import urllib2
import json

postcode_matcher = re.compile(r'^([A-PR-UWYZ]([0-9][0-9A-HJKPS-UW]?|[A-HK-Y][0-9][0-9ABEHMNPRV-Y]?)) ?([0-9][ABD-HJLNP-UW-Z]{2})$')

class Command(LabelCommand):
    help = 'Import postcode shapes'
    args = '<KML-DIRECTORY>'
    option_list = LabelCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        make_option('--verbose', action='store_true', dest='verbose', help='Provide verbose progress reporting')
    )

    def handle_label(self, directory_name, **options):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception, "No new generation to be used for import!"

        if not os.path.isdir(directory_name):
            raise Exception, "'%s' is not a directory" % (directory_name,)

        os.chdir(directory_name)

        if not glob("AB[0-9][0-9]*.kml"):
            raise Exception, "'%s' did not contain some of the expected postcode KML files" % (directory_name,)

        def verbose(s):
            if options['verbose']:
                print s.encode('utf-8')

        verbose("Loading from " + directory_name)

        files = sorted(os.listdir(directory_name))

        verbose("Got the sorted list of files")

        total_files = len(files)

        for i, e in enumerate(files):

            progress = "[%d%% complete] " % ((i * 100) / total_files,)

            if not e.endswith('.kml'):
                verbose("Ignoring non-KML file: " + e)
                continue

            postcode_with_space, _ = os.path.splitext(e)

            m = postcode_matcher.search(postcode_with_space)
            if not m:
                raise Exception, "Malfomed postcode: " + postcode_with_space

            postcode_without_sp = m.group(1) + m.group(3)

            kml_filename = os.path.join(directory_name, e)

            verbose(progress + "Loading " + unicode(os.path.realpath(kml_filename), 'utf-8'))

            ds = DataSource(kml_filename)
            layer = ds[0]
            if len(layer) != 1:
                raise Exception, "We only expect one feature in each layer"
            for feat in layer:

                

                area_code = 'O%02d' % (admin_level)

                    # FIXME: perhaps we could try to find parent areas
                    # via inclusion in higher admin levels
                    parent_area = None

                    try:
                        osm_code = Code.objects.get(type=code_type_osm, code=osm_id)
                    except Code.DoesNotExist:
                        osm_code = None

                    def update_or_create():
                        if osm_code:
                            m = osm_code.area
                        else:
                            m = Area(
                                name = name,
                                type = Type.objects.get(code=area_code),
                                country = Country.objects.get(code='G'),
                                parent_area = parent_area,
                                generation_low = new_generation,
                                generation_high = new_generation,
                            )

                        if m.generation_high and current_generation and m.generation_high.id < current_generation.id:
                            raise Exception, "Area %s found, but not in current generation %s" % (m, current_generation)
                        m.generation_high = new_generation

                        g = feat.geom.transform(4326, clone=True)

                        # In generating the data we should have
                        # excluded any "polygons" with less than four
                        # points (the final one being the same as the
                        # first), but just in case:
                        for polygon in g:
                            if g.num_points < 4:
                                return

                        poly = [ g ]

                        if options['commit']:
                            m.save()

                            if name not in kml_data.data:
                                print json.dumps(kml_data.data, sort_keys=True, indent=4)
                                raise Exception, u"Will fail to find '%s' in the dictionary" % (name,)

                            for k, v in kml_data.data[name].items():
                                language_name = None
                                if k == 'name':
                                    lang = 'default'
                                    language_name = "OSM Default"
                                else:
                                    name_match = re.search(r'^name:(.+)$', k)
                                    if name_match:
                                        lang = name_match.group(1)
                                        if lang in language_code_to_name:
                                            language_name = language_code_to_name[lang]
                                if not language_name:
                                    continue
                                # Otherwise, make sure that a NameType for this language exists:
                                NameType.objects.update_or_create({'code': lang},
                                                                  {'code': lang,
                                                                   'description': language_name})
                                name_type = NameType.objects.get(code=lang)
                                m.names.update_or_create({ 'type': name_type }, { 'name': v })
                            m.codes.update_or_create({ 'type': code_type_osm }, { 'code': osm_id })
                            save_polygons({ code : (m, poly) })

                    update_or_create()

class KML(ContentHandler):
    def __init__(self, *args, **kwargs):
        self.content = ''
        self.data = {}

    def characters(self, content):
        self.content += content

    def endElement(self, name):
        if name == 'name':
            self.current = {}
            self.data[normalize_whitespace(self.content)] = self.current
        elif name == 'value':
            self.current[self.name] = self.content.strip()
            self.name = None
        self.content = ''

    def startElement(self, name, attr):
        if name == 'Data':
            self.name = normalize_whitespace(attr['name'])
