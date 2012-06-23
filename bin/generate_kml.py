#!/usr/bin/python
# -*- coding: utf-8 -*-

from boundaries import *
from lxml import etree
from shapely.geometry import Polygon

def ways_overlap(a, b):
    """Determines if two Way objects represent overlapping polygons

    For example, if we have two overlapping ways:

    >>> w1 = Way('1', nodes=[Node('10', latitude=53, longitude=0),
    ...                      Node('11', latitude=53, longitude=4),
    ...                      Node('12', latitude=49, longitude=4),
    ...                      Node('13', latitude=49, longitude=0),
    ...                      Node('10', latitude=53, longitude=0)])

    >>> w2 = Way('2', nodes=[Node('14', latitude=51, longitude=2),
    ...                      Node('15', latitude=51, longitude=6),
    ...                      Node('16', latitude=47, longitude=6),
    ...                      Node('17', latitude=47, longitude=2),
    ...                      Node('14', latitude=51, longitude=2)])

    >>> ways_overlap(w1, w2)
    True

    Or a non-overlapping one:

    >>> w3 = Way('3', nodes=[Node('18', latitude=51, longitude=7),
    ...                      Node('19', latitude=51, longitude=11),
    ...                      Node('20', latitude=47, longitude=11),
    ...                      Node('21', latitude=47, longitude=7),
    ...                      Node('18', latitude=51, longitude=7)])
    >>> ways_overlap(w1, w3)
    False

    Passing in a Way with too few points is an error:

    >>> w_open = Way('4', nodes=[Node('18', latitude=51, longitude=7),
    ...                          Node('19', latitude=51, longitude=11)])
    >>> ways_overlap(w1, w_open)
    Traceback (most recent call last):
      ...
    ValueError: A LinearRing must have at least 3 coordinate tuples
    """

    tuples_a = [(float(n.lon), float(n.lat)) for n in a]
    tuples_b = [(float(n.lon), float(n.lat)) for n in b]
    polygon_a = Polygon(tuples_a)
    polygon_b = Polygon(tuples_b)
    return polygon_a.intersects(polygon_b)

def group_boundaries_into_polygons(outer_ways, inner_ways):

    """Group outer_ways and inner_ways into distinct polygons

    Given a list of ways that represent the outer and inner boundaries
    of possibly disconnected polygons, find how to group them into an
    outer way, and inner ways that represent holes in that outer
    boundary.

    For example:

    >>> big_square = Way('1', nodes=[Node('10', latitude=53, longitude=0),
    ...                              Node('11', latitude=53, longitude=4),
    ...                              Node('12', latitude=49, longitude=4),
    ...                              Node('13', latitude=49, longitude=0),
    ...                              Node('10', latitude=53, longitude=0)])
    >>>
    >>> hole_in_big_square = Way('2', nodes=[Node('14', latitude=52, longitude=1),
    ...                                      Node('15', latitude=52, longitude=3),
    ...                                      Node('16', latitude=50, longitude=3),
    ...                                      Node('17', latitude=50, longitude=1),
    ...                                      Node('14', latitude=52, longitude=1)])
    >>>
    >>> isolated_square = Way('3', nodes=[Node('18', latitude=52, longitude=-3),
    ...                                   Node('19', latitude=52, longitude=-2),
    ...                                   Node('20', latitude=51, longitude=-2),
    ...                                   Node('21', latitude=51, longitude=-3),
    ...                                   Node('18', latitude=52, longitude=-3)])
    >>> outers = [big_square, isolated_square]
    >>> inners = [hole_in_big_square]
    >>> grouped = group_boundaries_into_polygons(outers, inners)
    >>> for p in grouped:
    ...     print p
    {'outer': [Way(id="1", nodes=5)], 'inner': [Way(id="2", nodes=5)]}
    {'outer': [Way(id="3", nodes=5)], 'inner': []}

    Any Way object that has too few points is ignored:

    >>> too_small_a = Way('4', nodes=[Node('22', latitude=53, longitude=0)])
    >>> too_small_b = Way('5', nodes=[Node('23', latitude=53, longitude=0),
    ...                               Node('24', latitude=51, longitude=2)])
    >>> outers.append(too_small_a)
    >>> inners.insert(0, too_small_b)
    >>> grouped_with_invalid_ways = group_boundaries_into_polygons(outers, inners)
    >>> grouped == grouped_with_invalid_ways
    True

    """

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

    """Generate the contents of a KML files from Way objects

    For example, supposing we have these Ways:

    >>> big_square = Way('1', nodes=[Node('10', latitude=53, longitude=0),
    ...                              Node('11', latitude=53, longitude=4),
    ...                              Node('12', latitude=49, longitude=4),
    ...                              Node('13', latitude=49, longitude=0),
    ...                              Node('10', latitude=53, longitude=0)])
    >>>
    >>> hole_in_big_square = Way('2', nodes=[Node('14', latitude=52, longitude=1),
    ...                                      Node('15', latitude=52, longitude=3),
    ...                                      Node('16', latitude=50, longitude=3),
    ...                                      Node('17', latitude=50, longitude=1),
    ...                                      Node('14', latitude=52, longitude=1)])
    >>>
    >>> isolated_square = Way('3', nodes=[Node('18', latitude=52, longitude=-3),
    ...                                   Node('19', latitude=52, longitude=-2),
    ...                                   Node('20', latitude=51, longitude=-2),
    ...                                   Node('21', latitude=51, longitude=-3),
    ...                                   Node('18', latitude=52, longitude=-3)])
    >>> print kml_string('Example Folder',
    ...                  'Example Placemark',
    ...                  {"some key": "some value",
    ...                   "foo": "bar"},
    ...                  [big_square, isolated_square],
    ...                  [hole_in_big_square]),
    <?xml version='1.0' encoding='utf-8'?>
    <kml xmlns="http://earth.google.com/kml/2.1">
      <Folder>
        <name>Example Folder</name>
        <Placemark>
          <name>Example Placemark</name>
          <ExtendedData>
            <Data name="foo">
              <value>bar</value>
            </Data>
            <Data name="some key">
              <value>some value</value>
            </Data>
          </ExtendedData>
          <MultiGeometry>
            <Polygon>
              <outerBoundaryIs>
                <LinearRing>
                  <coordinates>0,53,0  4,53,0  4,49,0  0,49,0  0,53,0 </coordinates>
                </LinearRing>
              </outerBoundaryIs>
              <innerBoundaryIs>
                <LinearRing>
                  <coordinates>1,52,0  3,52,0  3,50,0  1,50,0  1,52,0 </coordinates>
                </LinearRing>
              </innerBoundaryIs>
            </Polygon>
            <Polygon>
              <outerBoundaryIs>
                <LinearRing>
                  <coordinates>-3,52,0  -2,52,0  -2,51,0  -3,51,0  -3,52,0 </coordinates>
                </LinearRing>
              </outerBoundaryIs>
            </Polygon>
          </MultiGeometry>
        </Placemark>
      </Folder>
    </kml>
    """

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
    """Return KML for a boundary represented by a supplied OSM element

    >>> big_square = Way('1', nodes=[Node('10', latitude=53, longitude=0),
    ...                              Node('11', latitude=53, longitude=4),
    ...                              Node('12', latitude=49, longitude=4),
    ...                              Node('13', latitude=49, longitude=0),
    ...                              Node('10', latitude=53, longitude=0)])
    >>> kml, bbox = get_kml_for_osm_element_no_fetch(big_square)
    >>> bbox
    [(49.0, 0.0, 53.0, 4.0)]
    >>> print kml, # +doctest: ELLIPSIS
    <?xml version='1.0' encoding='utf-8'?>
    <kml xmlns="http://earth.google.com/kml/2.1">
      <Folder>
        <name>Boundaries for Unknown name for way with ID 1 [way 1] from OpenStreetMap</name>
        <Placemark>
          <name>Unknown name for way with ID 1</name>
          <ExtendedData/>
          <MultiGeometry>
            <Polygon>
              <outerBoundaryIs>
                <LinearRing>
                  <coordinates>0,53,0  4,53,0  4,49,0  0,49,0  0,53,0 </coordinates>
                </LinearRing>
              </outerBoundaryIs>
            </Polygon>
          </MultiGeometry>
        </Placemark>
      </Folder>
    </kml>

    It is an error to pass in a Node instead of a Relation or a Way:

    >>> n = Node('1', latitude=51, longitude=0)
    >>> get_kml_for_osm_element_no_fetch(n)
    Traceback (most recent call last):
      ...
    Exception: Unsupported element type in get_kml_for_osm_element(node, 1)

    And it's an error to pass in an unclosed Way:

    >>> unclosed_way = Way('1', nodes=[Node('10', latitude=53, longitude=0),
    ...                              Node('11', latitude=53, longitude=4),
    ...                              Node('12', latitude=49, longitude=4)])
    >>> kml, bbox = get_kml_for_osm_element_no_fetch(unclosed_way)
    Traceback (most recent call last):
      ...
    UnclosedBoundariesException
    """

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

    """Fetch an OSM element (if necessary) and return KML

    For example, we could fetch the boundary of the South
    Cambridgeshire (which has a hole in it, which is Cambridge) with:

    >>> kml, bbox = get_kml_for_osm_element('relation', '295353')
    >>> print kml, #doctest: +ELLIPSIS
    <?xml version='1.0' encoding='utf-8'?>
    <kml xmlns="http://earth.google.com/kml/2.1">
      <Folder>
        <name>Boundaries for South Cambridgeshire [relation 295353] from OpenStreetMap</name>
        <Placemark>
          <name>South Cambridgeshire</name>
          <ExtendedData>
            <Data name="admin_level">
              <value>8</value>
            </Data>
            <Data name="boundary">
              <value>administrative</value>
            </Data>
            <Data name="name">
              <value>South Cambridgeshire</value>
            </Data>
            <Data name="ons_code">
              <value>12UG</value>
            </Data>
            <Data name="source:ons_code">
              <value>OS_OpenData_CodePoint Codelist.txt</value>
            </Data>
            <Data name="type">
              <value>boundary</value>
            </Data>
          </ExtendedData>
          <MultiGeometry>
            <Polygon>
              <outerBoundaryIs>
                <LinearRing>
                  <coordinates>...</coordinates>
                </LinearRing>
              </outerBoundaryIs>
              <innerBoundaryIs>
                <LinearRing>
                  <coordinates>...</coordinates>
                </LinearRing>
              </innerBoundaryIs>
            </Polygon>
          </MultiGeometry>
        </Placemark>
      </Folder>
    </kml>

    If a relation can't be found, (None, None) is returned:

    >>> get_kml_for_osm_element('relation', '100000000000')
    (None, None)
    """

    e = fetch_osm_element(element_type, element_id)
    if e is None:
        return (None, None)

    return get_kml_for_osm_element_no_fetch(e)


if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--test", dest="doctest",
                      default=False, action='store_true',
                      help="Run all doctests in this file")

    (options, args) = parser.parse_args()

    if args:
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    if options.doctest:
        import doctest
        failure_count, test_count = doctest.testmod()
        sys.exit(0 if failure_count == 0 else 1)
    else:
        parser.print_help(file=sys.stderr)
        sys.exit(1)
