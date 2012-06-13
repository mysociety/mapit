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
from BeautifulSoup import BeautifulSoup
from collections import namedtuple
import json

def make_missing_none(s):
    """If s is empty (considering Unicode spaces) return None, else s"""
    if re.search('(?uis)^\s*$', s):
        return None
    else:
        return s

LanguageCodes = namedtuple('LanguageCodes',
                           ['three_letter',
                            'two_letter',
                            'english_name',
                            'french_name'])

def get_iso639_2_table():
    """Scrape and return the table of ISO639-2 and ISO639-1 language codes

    The OSM tags of the form "name:en", "name:fr", etc. refer to
    ISO639-1 two-letter codes, or ISO639-2 three-letter codes.  This
    function parses the Library of Congress table of these values, and
    returns them as a list of LanguageCodes"""

    result = []
    url = "http://www.loc.gov/standards/iso639-2/php/code_list.php"
    f = urllib2.urlopen(url)
    data = f.read()
    f.close()
    soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
    table = soup.find('table', {'border': '1'})
    for row in table.findAll('tr', recursive=False):
        tds = row.findAll('td', recursive=False)
        if len(tds) != 4:
            continue
        strings = ["".join(td.findAll(text=True)).strip() for td in tds]
        result_row = LanguageCodes._make(make_missing_none(s) for s in strings)
        result.append(result_row)
    return result

class Command(LabelCommand):
    help = 'Import OSM administrative boundary data'
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

        if not glob("al[0-1][0-9]"):
            raise Exception, "'%s' did not contain any admin level directories (e.g. al02, al03, etc.)" % (directory_name,)

        def verbose(s):
            if options['verbose']:
                print s.encode('utf-8')

        verbose("Loading any admin boundaries from " + directory_name)

        verbose("Finding language codes...")

        language_code_to_name = {}
        code_keys = ('two_letter', 'three_letter')
        for row in get_iso639_2_table():
            english_name = getattr(row, 'english_name')
            for k in code_keys:
                code = getattr(row, k)
                if not code:
                    continue
                # Some of the language codes have a bibliographic or
                # terminology code, so strip those out:
                codes = re.findall(r'(\w+) \([BT]\)', code)
                if not codes:
                    codes = [code]
                for c in codes:
                    language_code_to_name[c] = english_name

        # print json.dumps(language_code_to_name, sort_keys=True, indent=4)

        for admin_level in range(2,12):

            verbose("Loading admin_level " + str(admin_level))

            admin_directory = "al%02d" % (admin_level)

            if not os.path.exists(admin_directory):
                verbose("Skipping the non-existent " + admin_directory)
                continue

            verbose("Loading all KML in " + admin_directory)

            for e in os.listdir(admin_directory):

                # if 'way-32291128' not in e:
                #     continue

                if not e.endswith('.kml'):
                    verbose("Ignoring non-KML file: " + e)
                    continue

                m = re.search(r'^(way|relation)-(\d+)-', e)
                if not m:
                    raise Exception, u"Couldn't extract OSM element type and ID from: " + e

                osm_type, osm_id = m.groups()

                kml_filename = os.path.join(admin_directory, e)

                verbose("Loading " + unicode(os.path.realpath(kml_filename), 'utf-8'))

                # Need to parse the KML manually to get the ExtendedData
                kml_data = KML()
                xml.sax.parse(kml_filename, kml_data)

                if osm_type == 'relation':
                    code_type_osm = CodeType.objects.get(code='osm_rel')
                elif osm_type == 'way':
                    code_type_osm = CodeType.objects.get(code='osm_way')
                else:
                    raise Exception, "Unknown OSM element type:", osm_type

                ds = DataSource(kml_filename)
                layer = ds[0]
                if len(layer) != 1:
                    raise Exception, "We only expect one feature in each layer"
                for feat in layer:
                    name = feat['Name'].value.decode('utf-8')
                    name = re.sub('\s+', ' ', name)
                    print " ", name.encode('utf-8')

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
            self.data[self.content.strip()] = self.current
        elif name == 'value':
            self.current[self.name] = self.content.strip()
            self.name = None
        self.content = ''

    def startElement(self, name, attr):
        if name == 'Data':
            self.name = attr['name']

