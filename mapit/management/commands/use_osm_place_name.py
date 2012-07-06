# use_osm_place_name.py:
#
# Look through KML files for any that have 'Unknown name for ...' as
# their name - if they have a place_name tag in their extended data,
# update the corresponding Area in the database with that name.
#
# Copyright (c) 2011, 2012 UK Citizens Online Democracy. All rights reserved.
# Email: mark@mysociety.org; WWW: http://www.mysociety.org

import os
import re
from optparse import make_option
from django.core.management.base import LabelCommand
from mapit.models import Area, Code, CodeType
from glob import glob
import urllib2
from lxml import etree

class Command(LabelCommand):
    help = 'Find any "Unknown" names, and use place_name instead, if possible'
    args = '<KML-DIRECTORY>'
    option_list = LabelCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        make_option('--verbose', action='store_true', dest='verbose', help='Provide verbose progress reporting')
    )

    def handle_label(self, directory_name, **options):

        if not os.path.isdir(directory_name):
            raise Exception, "'%s' is not a directory" % (directory_name,)

        os.chdir(directory_name)

        if not glob("al[0-1][0-9]"):
            raise Exception, "'%s' did not contain any admin level directories (e.g. al02, al03, etc.)" % (directory_name,)

        def verbose(s):
            if options['verbose']:
                print s.encode('utf-8')

        verbose("Loading any admin boundaries from " + directory_name)

        unknown_names_before = Area.objects.filter(name__startswith='Unknown name').count()

        for admin_level in range(2,12):

            verbose("Loading admin_level " + str(admin_level))

            admin_directory = "al%02d" % (admin_level)

            if not os.path.exists(admin_directory):
                verbose("Skipping the non-existent " + admin_directory)
                continue

            verbose("Loading all KML in " + admin_directory)

            files = sorted(os.listdir(admin_directory))
            total_files = len(files)

            for i, e in enumerate(files):

                progress = "[%d%% complete] " % ((i * 100) / total_files,)

                if not e.endswith('.kml'):
                    verbose("Ignoring non-KML file: " + e)
                    continue

                m = re.search(r'^(way|relation)-(\d+)-', e)
                if not m:
                    raise Exception, u"Couldn't extract OSM element type and ID from: " + e

                osm_type, osm_id = m.groups()

                kml_filename = os.path.join(admin_directory, e)

                if not re.search('Unknown name for', e):
                    continue

                verbose(progress + "Loading " + unicode(os.path.realpath(kml_filename), 'utf-8'))

                tree = etree.parse(kml_filename)
                place_name_values = tree.xpath('//kml:Placemark/kml:ExtendedData/kml:Data[@name="place_name"]/kml:value',
                                               namespaces={'kml': 'http://earth.google.com/kml/2.1'} )

                if len(place_name_values) > 0:

                    place_name = place_name_values[0].text

                    verbose(u"Found a better name: " + place_name)

                    # Then we can replace the name:

                    if osm_type == 'relation':
                        code_type_osm = CodeType.objects.get(code='osm_rel')
                    elif osm_type == 'way':
                        code_type_osm = CodeType.objects.get(code='osm_way')
                    else:
                        raise Exception, "Unknown OSM element type:", osm_type

                    try:
                        existing_area = Code.objects.get(type=code_type_osm, code=osm_id).area
                    except Code.DoesNotExist:
                        print "WARNING: failed to find Code with code_type %s and code %s" % (code_type_osm, osm_id)
                        continue

                    # Just check that the existing area really does
                    # still have an unknown name:

                    if not existing_area.name.startswith('Unknown name'):
                        print (u"The existing area already had a sensible name: " + existing_area.name).encode('utf-8')
                        raise Exception, "Not overwriting sensible name, exiting."

                    existing_area.name = place_name

                    if options['commit']:
                        existing_area.save()

        unknown_names_after = Area.objects.filter(name__startswith='Unknown name').count()

        print "unknown_names_before:", unknown_names_before
        print "unknown_names_after:", unknown_names_after
