#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script fetches all administrative boundaries from OpenStreetMap
# (at any admin level) and writes them out as KML.

import xml.sax, urllib, os, re, errno, sys, time
from xml.sax.handler import ContentHandler
import urllib, urllib2

from boundaries import *
from generate_kml import *

if len(sys.argv) < 2 or len(sys.argv) > 3:
    print >> sys.stderr, "Usage: %s <PLANET> [LARGEST-ADMIN-LEVEL]" % (sys.argv[0],)
    sys.exit(1)

planet_filename = sys.argv[1]

start_admin_level = 2
if len(sys.argv) == 3:
    start_admin_level = int(sys.argv[2])

dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(dir, '..', 'data')

def replace_slashes(s):
    return re.sub(r'/', '_', s)

for admin_level in range(start_admin_level, 12):




    print "Fetching data at admin level", admin_level

    predicate = '["boundary"="administrative"]'
    predicate += '["admin_level"="%d"]' % (admin_level,)
    data = timeout + '(relation%s;way%s;);out body;' % (predicate, predicate)

    print "data is:", data

    file_basename = "admin-level-%02d-worldwide.xml" % (admin_level,)
    xml_filename = os.path.join(data_dir, "cache", file_basename)
    overpass_post_request(data, xml_filename)

    level_directory = os.path.join(data_dir, "cache", "al%02d" % (admin_level,))
    mkdir_p(level_directory)

    def handle_top_level_element(element_type, element_id, tags):

        if 'admin_level' not in tags:
            return
        if tags['admin_level'] != str(admin_level):
            return

        name = get_name_from_tags(tags, element_type, element_id)

        print "Considering admin boundary:", name.encode('utf-8')

        try:

            basename = "%s-%s-%s" % (element_type,
                                     element_id,
                                     replace_slashes(name))

            filename = os.path.join(level_directory, u"%s.kml" % (basename,))

            if not os.path.exists(filename):

                while True:
                    
                    try:

                        kml, _ = get_kml_for_osm_element(element_type, element_id)
                        if not kml:
                            print "      No data found for %s %s" % (element_type, element_id)
                            return

                        print "      Writing KML to", filename.encode('utf-8')
                        with open(filename, "w") as fp:
                            fp.write(kml)

                    except UnclosedBoundariesException, e:
                        raise e
                    except Exception, e:
                        # Wait before trying again:
                        time.sleep(wait_after_exceptions)
                        email_me("error while scraping OSM boundaries",
                                 unicode(e).encode('utf-8')+"\n"+element_type+"/"+str(element_id),
                                 'mark@eclipse.ukcod.org.uk',
                                 'mark-osmscrape@longair.net')
                    break

        except UnclosedBoundariesException:
            print "      ... ignoring unclosed boundary"

    parse_xml_minimal(xml_filename, handle_top_level_element)
