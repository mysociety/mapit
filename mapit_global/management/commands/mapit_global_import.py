# import_global_osm.py:
#
# This script is used to import boundaries from OpenStreetMap into
# MaPit.
#
# It takes KML data generated either by
# get-boundaries-by-admin-level.py, so you need to have run that
# script first.
#
# This script was originally based on import_norway_osm.py by Matthew
# Somerville.
#
# Copyright (c) 2011, 2012 UK Citizens Online Democracy. All rights reserved.
# Email: mark@mysociety.org; WWW: http://www.mysociety.org

from collections import namedtuple
import csv
from glob import glob
import json
import os
import re
import xml.sax

from django.core.management.base import LabelCommand
# Not using LayerMapping as want more control, but what it does is what this does
# from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource
from django.utils.six.moves import urllib
from django.utils.encoding import smart_str, smart_text

import shapely

from mapit.models import Area, Generation, Country, Type, Code, CodeType, NameType
from mapit.management.command_utils import save_polygons, KML
from mapit.management.command_utils import fix_invalid_geos_multipolygon


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
    url = "http://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt"
    for row in csv.reader(urllib.request.urlopen(url), delimiter='|'):
        row = [cell.decode('utf-8-sig') for cell in row]
        bibliographic = [row[0], row[2], row[3], row[4]]
        result_row = LanguageCodes._make(make_missing_none(s) for s in bibliographic)
        result.append(result_row)
        if row[1]:
            terminologic = [row[1], row[2], row[3], row[4]]
            result_row = LanguageCodes._make(make_missing_none(s) for s in terminologic)
            result.append(result_row)
    return result


class Command(LabelCommand):
    help = 'Import OSM boundary data from KML files'
    args = '<KML-DIRECTORY>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle_label(self, directory_name, **options):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception("No new generation to be used for import!")

        if not os.path.isdir(directory_name):
            raise Exception("'%s' is not a directory" % (directory_name,))

        os.chdir(directory_name)

        mapit_type_glob = smart_text("[A-Z0-9][A-Z0-9][A-Z0-9]")

        if not glob(mapit_type_glob):
            raise Exception(
                "'%s' did not contain any directories that look like MapIt types (e.g. O11, OWA, etc.)" % (
                    directory_name,))

        def verbose(s):
            if int(options['verbosity']) > 1:
                print(smart_str(s))

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
                language_code_to_name[code] = english_name

        global_country = Country.objects.get(code='G')

        # print json.dumps(language_code_to_name, sort_keys=True, indent=4)

        skip_up_to = None
        # skip_up_to = 'relation-80370'

        skipping = bool(skip_up_to)

        for type_directory in sorted(glob(mapit_type_glob)):

            verbose("Loading type " + type_directory)

            if not os.path.exists(type_directory):
                verbose("Skipping the non-existent " + type_directory)
                continue

            verbose("Loading all KML in " + type_directory)

            files = sorted(os.listdir(type_directory))
            total_files = len(files)

            for i, e in enumerate(files):

                progress = "[%d%% complete] " % ((i * 100) / total_files,)

                if skipping:
                    if skip_up_to in e:
                        skipping = False
                    else:
                        continue

                if not e.endswith('.kml'):
                    verbose("Ignoring non-KML file: " + e)
                    continue

                m = re.search(r'^(way|relation)-(\d+)-', e)
                if not m:
                    raise Exception("Couldn't extract OSM element type and ID from: " + e)

                osm_type, osm_id = m.groups()

                kml_filename = os.path.join(type_directory, e)

                verbose(progress + "Loading " + os.path.realpath(kml_filename))

                # Need to parse the KML manually to get the ExtendedData
                kml_data = KML()
                xml.sax.parse(smart_str(kml_filename), kml_data)

                useful_names = [n for n in kml_data.data.keys() if not n.startswith('Boundaries for')]
                if len(useful_names) == 0:
                    raise Exception("No useful names found in KML data")
                elif len(useful_names) > 1:
                    raise Exception("Multiple useful names found in KML data")
                name = useful_names[0]
                print(smart_str("  %s" % name))

                if osm_type == 'relation':
                    code_type_osm = CodeType.objects.get(code='osm_rel')
                elif osm_type == 'way':
                    code_type_osm = CodeType.objects.get(code='osm_way')
                else:
                    raise Exception("Unknown OSM element type: " + osm_type)

                ds = DataSource(kml_filename)
                layer = ds[0]
                if len(layer) != 1:
                    raise Exception("We only expect one feature in each layer")

                feat = layer[1]

                g = feat.geom.transform(4326, clone=True)

                if g.geom_count == 0:
                    # Just ignore any KML files that have no polygons in them:
                    verbose('    Ignoring that file - it contained no polygons')
                    continue

                # Nowadays, in generating the data we should have
                # excluded any "polygons" with less than four points
                # (the final one being the same as the first), but
                # just in case:
                polygons_too_small = 0
                for polygon in g:
                    if polygon.num_points < 4:
                        polygons_too_small += 1
                if polygons_too_small:
                    message = "%d out of %d polygon(s) were too small" % (polygons_too_small, g.geom_count)
                    verbose('    Skipping, since ' + message)
                    continue

                g_geos = g.geos

                if not g_geos.valid:
                    verbose("    Invalid KML:" + kml_filename)
                    fixed_multipolygon = fix_invalid_geos_multipolygon(g_geos)
                    if len(fixed_multipolygon) == 0:
                        verbose("    Invalid polygons couldn't be fixed")
                        continue
                    g = fixed_multipolygon.ogr

                area_type = Type.objects.get(code=type_directory)

                try:
                    osm_code = Code.objects.get(type=code_type_osm,
                                                code=osm_id,
                                                area__generation_high__lte=current_generation,
                                                area__generation_high__gte=current_generation)
                except Code.DoesNotExist:
                    verbose('    No area existed in the current generation with that OSM element type and ID')
                    osm_code = None

                was_the_same_in_current = False

                if osm_code:
                    m = osm_code.area

                    # First, we need to check if the polygons are
                    # still the same as in the previous generation:
                    previous_geos_geometry = m.polygons.collect()
                    if previous_geos_geometry is None:
                        verbose('    In the current generation, that area was empty - skipping')
                    else:
                        # Simplify it to make sure the polygons are valid:
                        previous_geos_geometry = shapely.wkb.loads(
                            str(previous_geos_geometry.simplify(tolerance=0).ewkb))
                        new_geos_geometry = shapely.wkb.loads(str(g.geos.simplify(tolerance=0).ewkb))
                        if previous_geos_geometry.almost_equals(new_geos_geometry, decimal=7):
                            was_the_same_in_current = True
                        else:
                            verbose('    In the current generation, the boundary was different')

                if was_the_same_in_current:
                    # Extend the high generation to the new one:
                    verbose('    The boundary was identical in the previous generation; raising generation_high')
                    m.generation_high = new_generation

                else:
                    # Otherwise, create a completely new area:
                    m = Area(
                        name=name,
                        type=area_type,
                        country=global_country,
                        parent_area=None,
                        generation_low=new_generation,
                        generation_high=new_generation,
                    )

                poly = [g]

                if options['commit']:
                    m.save()
                    verbose('    Area ID: ' + str(m.id))

                    if name not in kml_data.data:
                        print(json.dumps(kml_data.data, sort_keys=True, indent=4))
                        raise Exception("Will fail to find '%s' in the dictionary" % (name,))

                    old_lang_codes = set(n.type.code for n in m.names.all())

                    for k, translated_name in kml_data.data[name].items():
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
                        old_lang_codes.discard(lang)

                        # Otherwise, make sure that a NameType for this language exists:
                        NameType.objects.update_or_create(code=lang, defaults={'description': language_name})
                        name_type = NameType.objects.get(code=lang)

                        m.names.update_or_create(type=name_type, defaults={'name': translated_name})

                    if old_lang_codes:
                        verbose('Removing deleted languages codes: ' + ' '.join(old_lang_codes))
                    m.names.filter(type__code__in=old_lang_codes).delete()
                    # If the boundary was the same, the old Code
                    # object will still be pointing to the same Area,
                    # which just had its generation_high incremented.
                    # In every other case, there's a new area object,
                    # so create a new Code and save it:
                    if not was_the_same_in_current:
                        new_code = Code(area=m, type=code_type_osm, code=osm_id)
                        new_code.save()
                    save_polygons({'dummy': (m, poly)})
