#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script fetches all administrative boundaries from OpenStreetMap
# (at any admin level) and writes them out as KML.

import xml.sax, urllib, os, re, errno, sys, time
from xml.sax.handler import ContentHandler
import urllib, urllib2

from boundaries import *
from generate_kml import *

from lxml import etree

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

def write_element_to_cached_xml(element):
    filename = get_cache_filename(*element.name_id_tuple())
    if os.path.exists(filename):
        return
    with open(filename, 'w') as fp:
        fp.write(etree.tostring(element.to_xml(include_node_dependencies=True),
                                pretty_print=True,
                                encoding="utf-8",
                                xml_declaration=True))

def wanted_boundary(element):
    boundary = element.tags.get('boundary', '')
    if boundary != 'administrative':
        return None
    admin_level = element.tags.get('admin_level', '')
    # if admin_level != '4':
    if not admin_level:
        return None
    if element.element_type == 'node':
        return None
    return admin_level

def write_kml(element, admin_level):
    element_type, element_id = element.name_id_tuple()
    name = get_name_from_tags(element.tags, element_type, element_id)
    try:
        basename = "%s-%s-%s" % (element_type,
                                 element_id,
                                 replace_slashes(name))

        level_directory = os.path.join(data_dir, "cache", "planet-al%02d" % (int(admin_level,10),))
        mkdir_p(level_directory)
        filename = os.path.join(level_directory, u"%s.kml" % (basename,))

        if not os.path.exists(filename):

            kml, _ = get_kml_for_osm_element_no_fetch(element)
            if not kml:
                print "      No data found for %s %s" % (element_type, element_id)
                return

            print "      Writing KML to", filename.encode('utf-8')
            with open(filename, "w") as fp:
                fp.write(kml)

    except UnclosedBoundariesException:
        print "      ... ignoring unclosed boundary"

def write_kml_if_wanted_element(element):
    admin_level = wanted_boundary(element)
    if admin_level:
        write_kml(element, admin_level)

def deal_with_top_level_element(element, parser):

    global elements_parsed
    elements_parsed += 1
    if (elements_parsed % 10000) == 0:
        print "Time through:", time_through, ", parsed", elements_parsed, "elements"

    element_tuple = element.name_id_tuple()
    element_type, element_id = element_tuple

    debug = element_id == "139312403"

    # Nodes are a special case - there are too many of them to deal
    # with in the same way as ways / relations, since if we created
    # one file per node we would quickly run out of inodes in the
    # filesystem.  Instead, we output all nodes in the file with the
    # way that includes them.
    if element_type == 'node':
        if element_id in nodes_needed:
            nodes_needed[element_id] = element
        return

    # Now we know we're only dealing with ways or relations.

    # When admin_level is truthy, this is an element that we
    # ultimately want to write out as KML:

    admin_level = wanted_boundary(element)

    # If this way / relation is marked as incomplete from a previous
    # round, we need to check if that is still the case (i.e. whether
    # it can now be completely reconstructed).

    if debug: print "admin_level is:", admin_level

    if element_tuple in incomplete_ways_or_relations:

        if debug: print "was in incomplete_ways_or_relations"

        still_missing = element.reconstruct_missing(parser, nodes_needed)
        if debug: print "still_missing is:", still_missing
        if still_missing:
            # It was marked as incomplete, and is still incomplete:
            if element_type == 'way':
                # Make sure that every node is in nodes_needed for the
                # next time through:
                for node in element:
                    if debug:  "adding node", node.element_id
                    new_nodes_needed[node.element_id] = None
            elif element_type == 'relation':
                for member, role in element:
                    if role in OSMXMLParser.IGNORED_ROLES:
                        continue
                    if member.element_content_missing:
                        member_tuple = member.name_id_tuple()
                        member_type, member_id = member_tuple
                        if member_type == 'node':
                            new_nodes_needed[member_id] = None
                        else:
                            incomplete_ways_or_relations.add(member_tuple)
        else: # i.e. it's complete
            write_element_to_cached_xml(element)
            incomplete_ways_or_relations.discard(element_tuple)
            if admin_level:
                write_kml(element, admin_level)
    else:

        if debug: print "wasn't in incomplete_ways_or_relations"
        # If this is a wanted boundary, it might be one we've never seen before.
        if admin_level:

            # If there's a version from the filesystem, that will be
            # more complete:
            from_cache = parser.get_known_or_fetch(element_type, element_id)
            if not from_cache.element_content_missing:
                element = from_cache

            still_missing = element.reconstruct_missing(parser, nodes_needed)
            if still_missing:
                incomplete_ways_or_relations.add(element_tuple)
                for missing_element in still_missing:
                    missing_type, missing_id = missing_element.name_id_tuple()
                    if missing_id == "144804249":
                        print "  got our one (missing element)!"
                    if missing_type == 'node':
                        new_nodes_needed[missing_id] = None
                    else:
                        incomplete_ways_or_relations.add(missing_element.name_id_tuple())
            else: # i.e. it's complete
                write_element_to_cached_xml(element)
                write_kml(element, admin_level)

nodes_needed = {}
new_nodes_needed = {}
incomplete_ways_or_relations = set()

time_through = 1

# import pdb; pdb.set_trace()

while True:

    print "###### Starting parsing..."
    elements_parsed = 0

    print "At start of run, len(nodes_needed) is:", len(nodes_needed)

    print "... and incomplete_ways_or_relations are:"
    for element in sorted(incomplete_ways_or_relations):
        print "  ", element

    parser = OSMXMLParser(fetch_missing=False, callback=deal_with_top_level_element, cache_in_memory=False)
    with open(planet_filename) as fp:
        xml.sax.parse(fp, parser)

    if not (new_nodes_needed or incomplete_ways_or_relations):
        "Everything found, exiting."
        break

    nodes_needed = new_nodes_needed
    new_nodes_needed = {}

    time_through += 1

    # if time_through > 3:
    #     break
