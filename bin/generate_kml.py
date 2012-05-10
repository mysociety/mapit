#!/usr/bin/python
# -*- coding: utf-8 -*-

from boundaries import *
from lxml import etree

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

    all_ways = [(w, False) for w in outer_ways]
    all_ways += [(w, True) for w in inner_ways]

    polygon = etree.SubElement(placemark, "Polygon")
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

def main():

    # relation_id = '375982' # Orkney
    relation_id = '295353' # South Cambridgeshire

    parsed_relation = fetch_osm_element('relation', relation_id)
    outer_ways = join_way_soup(parsed_relation.way_iterator(False))
    inner_ways = join_way_soup(parsed_relation.way_iterator(True))

    print kml_string(u"Norway OSM boundaries",
                     u"Akershus",
                     {u"ref": u"02",
                      u"osm": u"406106",
                      u"name:ru": u"Акерсхус"},
                     outer_ways,
                     inner_ways)

if __name__ == "__main__":
    main()
