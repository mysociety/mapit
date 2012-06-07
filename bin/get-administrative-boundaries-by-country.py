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
        if e.element_type == "relation":
            for member, role in e:
                contained_elements.add(member.name_id_tuple())
    return [e for e in elements if e not in contained_elements]

# Fetch all relations and ways that are tagged with
# boundary=administrative and admin_level=2:

l2_predicate = '["boundary"="administrative"]["admin_level"="2"]'
data = timeout + 'relation%s;way%s;);out body;' % (l2_predicate, l2_predicate)

l2_xml_filename = os.path.join(data_dir, "cache", "admin-level-2-relations.xml")
overpass_post_request(data, l2_xml_filename)

all_l2_elements = parse_xml(l2_xml_filename, False)

non_contained_l2_elements = get_non_contained_elements(all_l2_elements)

countries_directory = os.path.join(data_dir, "countries")
mkdir_p(countries_directory)

# This loop (approximately) iterates over relations that represent
# country borders.  There are some unclosed borders and non-nations
# still, but we won't worry about them for the moment.

for e in non_contained_l2_elements:

    name = e.get_name()
    print "######", name
    element_tuple = e.name_id_tuple()

    print name.encode('utf-8')
    # if name != "Switzerland":
    #     continue

    print "http://www.openstreetmap.org/browse/%s/%s" % element_tuple

    # Create a directory for each country:

    country_basename = "%s-%s-%s" % ((name,) + element_tuple)

    country_directory = os.path.join(countries_directory, country_basename)
    print "ensuring the existence of the directory:", country_directory
    mkdir_p(country_directory)

    # Output KML representing the country border:

    try:
        kml_for_element, bounding_boxes = get_kml_for_osm_element(*element_tuple)
        kml_filename = os.path.join(country_directory, country_basename + ".kml")
    except UnclosedBoundariesException, e:
        print "The boundary was unclosed - more details below:"
        print e.detailed_error
        continue

    with open(kml_filename, "w") as fp:
        fp.write(kml_for_element)

    # Now go through each admin_level for the current country, and
    # fetch all boundaries within the country's bounding boxes.

    for admin_level in range(3, 12):

        print "  fetching data at admin level", admin_level

        level_directory = os.path.join(country_directory,"al"+str(admin_level))
        mkdir_p(level_directory)

        for bbox in bounding_boxes:

            predicate = '["boundary"="administrative"]'
            predicate += '["admin_level"="%d"]' % (admin_level,)
            predicate += '(%f,%f,%f,%f);' % bbox

            data = timeout + "(relation%sway%s>;);out body;" % (predicate, predicate)
            print "    data is:", data

            filename = os.path.join(country_directory, u"%s-%s-al%d.xml" % (element_tuple + (admin_level,)))
            overpass_post_request(data, filename)
            print "    parsing from:", filename.encode('utf-8')
            parsed_elements = parse_xml(filename)

            for possible_admin_boundary in get_non_contained_elements(parsed_elements):

                # The bounding box query is somewhat annoying - it
                # will fetch relations that directly include a node in
                # the bounding box, or ones that directly include a
                # way that contains a node in the bounding box.  So,
                # this query returns lots of ways and relations that
                # are incomplete (unclosed), and we have to ignore
                # them.

                # In addition, one concern is that with the bounding
                # box query we may miss some relations entirely,
                # because they only contain ways or nodes that overlap
                # with the bounding box via intermediate relations.

                if 'admin_level' not in possible_admin_boundary.tags:
                    continue
                if possible_admin_boundary.tags['admin_level'] != str(admin_level):
                    continue

                print "      possible_admin_boundary is:", possible_admin_boundary.get_name().encode('utf-8')

                try:

                    kml, _ = get_kml_for_osm_element(*possible_admin_boundary.name_id_tuple())

                    filename = os.path.join(level_directory, u"%s.kml" % (replace_slashes(possible_admin_boundary.get_name())))
                    print "      Writing KML to", filename.encode('utf-8')
                    with open(filename, "w") as fp:
                        fp.write(kml)

                except UnclosedBoundariesException:
                    print "      ... ignoring unclosed boundary"
