#!/usr/bin/python
# -*- coding: utf-8 -*-

from boundaries import *
from lxml import etree
from shapely.geometry import Polygon

def ways_overlap(a, b):
    tuples_a = [(float(n.lon), float(n.lat)) for n in a]
    tuples_b = [(float(n.lon), float(n.lat)) for n in b]
    polygon_a = Polygon(tuples_a)
    polygon_b = Polygon(tuples_b)
    return polygon_a.intersects(polygon_b)

def group_boundaries_into_polygons(outer_ways, inner_ways):

    """Group outer_ways and inner_ways into distinct polygons"""

    # For each outer boundary, find all the inner paths that overlap
    # with it, and remove them from the list of inner paths to consider:

    result = []
    inner_ways_left = inner_ways[:]

    for outer_way in outer_ways:
        if len(outer_way) < 3:
            continue
        polygon = { 'outer': [outer_way],
                    'inner': [] }
        for i in range(len(inner_ways_left) - 1, -1, -1):
            inner_way = inner_ways_left[i]
            if len(inner_way) < 3:
                del inner_ways_left[i]
                continue
            if ways_overlap(inner_way, outer_way):
                polygon['inner'].append(inner_way)
                del inner_ways_left[i]
        result.append(polygon)

    return result

def kml_string(folder_name,
               placemark_name,
               extended_data,
               outer_ways,
               inner_ways):

    kml = etree.Element("kml",
                        nsmap={None: "http://earth.google.com/kml/2.1"})
    folder = etree.SubElement(kml,"Folder")
    name = etree.SubElement(folder,"name")
    name.text = folder_name

    placemark = etree.SubElement(folder,"Placemark")
    name = etree.SubElement(placemark,"name")
    name.text = placemark_name

    extended = etree.SubElement(placemark, "ExtendedData")
    for k, v in sorted(extended_data.items()):
        data = etree.SubElement(extended, "Data",
                                attrib={"name": k})
        value = etree.SubElement(data, "value")
        value.text = v

    multigeometry = etree.SubElement(placemark, "MultiGeometry")

    for p in group_boundaries_into_polygons(outer_ways, inner_ways):
        polygon = etree.SubElement(multigeometry, "Polygon")
        all_ways = [(w, False) for w in p['outer']]
        all_ways += [(w, True) for w in p['inner']]
        for way, inner in all_ways:
            boundary_type = "inner" if inner else "outer"
            boundary = etree.SubElement(polygon, boundary_type+"BoundaryIs")
            linear_ring = etree.SubElement(boundary, "LinearRing")
            coordinates = etree.SubElement(linear_ring, "coordinates")
            coordinates.text = " ".join("%s,%s,0 " % n.lon_lat_tuple() for n in way.nodes)

    return etree.tostring(kml,
                          pretty_print=True,
                          encoding="utf-8",
                          xml_declaration=True)


def get_kml_for_osm_element_no_fetch(element):

    element_type, element_id = element.name_id_tuple()

    name = element.get_name()
    folder_name = u"Boundaries for %s [%s %s] from OpenStreetMap" % (name, element_type, element_id)

    if element_type == 'way':
        if not element.closed():
            raise UnclosedBoundariesException, "get_kml_for_osm_element called with an unclosed way (%s)" % (element_id)
        return (kml_string(folder_name,
                           name,
                           element.tags,
                           [element],
                           []),
                [element.bounding_box_tuple()])

    elif element_type == 'relation':

        outer_ways = join_way_soup(element.way_iterator(False))
        inner_ways = join_way_soup(element.way_iterator(True))

        bounding_boxes = [w.bounding_box_tuple() for w in outer_ways]

        extended_data = element.tags.copy()
        extended_data['osm'] = element_id

        return (kml_string(folder_name,
                           name,
                           element.tags,
                           outer_ways,
                           inner_ways),
                bounding_boxes)

    else:
        raise Exception, "Unsupported element type in get_kml_for_osm_element(%s, %s)" % (element_type, element_id)

def get_kml_for_osm_element(element_type, element_id):

    e = fetch_osm_element(element_type, element_id)
    if e is None:
        return (None, None)

    return get_kml_for_osm_element_no_fetch(e)

def main():

    # relation_id = '375982' # Orkney
    relation_id = '295353' # South Cambridgeshire

    kml, bboxes = get_kml_for_osm_element('relation', relation_id)

    print kml

if __name__ == "__main__":
    main()
