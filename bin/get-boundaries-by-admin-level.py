#!/usr/bin/python
# -*- coding: utf-8 -*-

# This script fetches all administrative boundaries from OpenStreetMap
# (at any admin level) and writes them out as KML.

import xml.sax, urllib, os, re, errno, sys
from xml.sax.handler import ContentHandler
import urllib, urllib2

from boundaries import *
from generate_kml import *

dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(dir, '..', 'data')

timeout = '[timeout:3600];'

def overpass_post_request(data, filename):
    """Make an Overpass API call and write to filename (if it doesn't exist)"""
    if not os.path.exists(filename):
        url = 'http://www.overpass-api.de/api/interpreter'
        values = {'data': data}
        encoded_values = urllib.urlencode(values)
        request = urllib2.Request(url, encoded_values)
        response = urllib2.urlopen(request)
        with open(filename, "w") as fp:
            fp.write(response.read())

def replace_slashes(s):
    return re.sub(r'/', '_', s)

def get_non_contained_elements(elements):
    """Filter elements, keeping only those which are not a member of another"""
    contained_elements = set([])
    for e in elements:
        if e.get_element_name() == "relation":
            for member, role in e:
                contained_elements.add(member.name_id_tuple())
    return [e for e in elements if e not in contained_elements]

for admin_level in range(2, 12):

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

    for e in get_non_contained_elements(parse_xml(xml_filename, False)):

        if 'admin_level' not in e.tags:
            continue
        if e.tags['admin_level'] != str(admin_level):
            continue

        print "Considering admin boundary:", e.get_name().encode('utf-8')

        try:

            element_type, element_id = e.name_id_tuple()

            kml, _ = get_kml_for_osm_element(element_type, element_id)

            basename = "%s-%s-%s" % (element_type,
                                     element_id,
                                     replace_slashes(e.get_name()))

            filename = os.path.join(level_directory, u"%s.kml" % (basename,))
            print "      Writing KML to", filename.encode('utf-8')
            with open(filename, "w") as fp:
                fp.write(kml)

        except UnclosedBoundariesException:
            print "      ... ignoring unclosed boundary"
