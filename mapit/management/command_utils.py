# Shared functions for postcode and area importing.

import re
import sys
from xml.sax.handler import ContentHandler
import shapely.ops
import shapely.wkt
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon


class KML(ContentHandler):
    def __init__(self, *args, **kwargs):
        self.content = ''
        self.data = {}

    def characters(self, content):
        self.content += content

    @staticmethod
    def normalize_whitespace(s):
        return re.sub('(?us)\s+', ' ', s).strip()

    def endElement(self, name):
        if name == 'name':
            self.current = {}
            self.data[self.normalize_whitespace(self.content)] = self.current
        elif name == 'value':
            self.current[self.name] = self.content.strip()
            self.name = None
        self.content = ''

    def startElement(self, name, attr):
        if name == 'Data':
            self.name = self.normalize_whitespace(attr['name'])


def save_polygons(lookup):
    for shape in lookup.values():
        m, poly = shape
        if not poly:
            continue
        sys.stdout.write(".")
        sys.stdout.flush()
        # g = OGRGeometry(OGRGeomType('MultiPolygon'))
        m.polygons.all().delete()
        for p in poly:
            if p.geom_name == 'POLYGON':
                shapes = [p]
            else:
                shapes = p
            for g in shapes:
                # Ignore any shape with fewer than four points, to
                # avoid introducing invalid polygons into the
                # database.
                if g.point_count < 4:
                    continue
                # Make sure it is two-dimensional
                g.coord_dim = 2
                m.polygons.create(polygon=g.wkb)
        # m.polygon = g.wkt
        # m.save()
        # Clear the polygon's list, so that if it has both an ons_code and unit_id, it's not processed twice
        poly[:] = []
    print("")


def fix_with_buffer(geos_polygon):
    return geos_polygon.buffer(0)


def fix_with_exterior_union_polygonize(geos_polygon):
    exterior_ring = geos_polygon.exterior_ring
    unioned = exterior_ring.union(exterior_ring)
    # We want to use GEOSPolygonize which isn't exposed via
    # django.contrib.gis.geos, but is available via shapely:
    shapely_unioned = shapely.wkt.loads(unioned.wkt)
    try:
        reconstructed_geos_polygons = [
            GEOSGeometry(sp.wkt, geos_polygon.srid) for sp in
            shapely.ops.polygonize(shapely_unioned)]
    except ValueError:
        reconstructed_geos_polygons = []
    return MultiPolygon(reconstructed_geos_polygons)


def fix_invalid_geos_polygon(geos_polygon, methods=('buffer', 'exterior')):
    """Try to make a valid version of an invalid GEOS polygon

    The test cases and techniques used here are from the helpful
    presentation here: http://s3.opengeo.org/postgis-power.pdf

      3  ------>------
         |           |
         |           |
      2  |     x     |
         |    / \    |
         ^   /   \   |
      1  |  x     x  |
         |   \   /   |
         |    \ /    |
      0  --<--| |---<--

         0  1  2  3  4

    This is the "banana polygon" example, if you imagine the points at
    (2, 0) drawn together to be the same point.

    >>> from django.contrib.gis.geos import Polygon
    >>> coords = [(0, 0), (0, 3), (4, 3), (4, 0),
    ...           (2, 0), (3, 1), (2, 2), (1, 1),
    ...           (2, 0), (0, 0)]
    >>> poly = Polygon(coords)
    >>> poly.valid
    False

    That one should be fixable just with the ST_Buffer(_, 0) technique:

    >>> fixed = fix_invalid_geos_polygon(poly, 'buffer')
    >>> fixed.valid
    True
    >>> len(fixed)
    2
    >>> import math
    >>> expected_length = 3 + 3 + 4 + 4 + 4 * math.sqrt(2)
    >>> abs(fixed.length - expected_length) < 0.000001
    True

    Others need the more complex technique mentioned in that PDF, such
    as this figure-of-eight polygon:

      2         -->--
               |     |
               |     |
      1   --<-----<--
         |     |
         |     |
      0   -->--

         0     1     2

    ... with coordinates as follows:

    >>> coords = [(0, 0), (1, 0), (1, 2), (2, 2),
    ...           (2, 1), (0, 1), (0, 0)]
    >>> poly = Polygon(coords)
    >>> poly.valid
    False

    The function should return a valid version with the right
    perimeter length:

    >>> fixed = fix_invalid_geos_polygon(poly, ('buffer', 'exterior'))
    >>> fixed.valid
    True
    >>> fixed.length
    8.0

    Also, check that this can fix a invalid polygon that's equivalent
    to four separate polygons:

      2  ---x---
         | / \ |
         |/   \|
      1  x     x
         |\   /|
         | \ / |
      0  ---x---

         0  1  2

    ... where the points start at the bottom 'x', go right around the
    outside square clockwise and then go around the inside square
    anti-clockwise, creating 4 filled triangles with a square hole in
    the middle:

    >>> coords = [(1, 0), (0, 0), (0, 2), (2, 2), (2, 0), (1, 0),
    ...           (2, 1), (1, 2), (0, 1), (1, 0)]
    >>> poly = Polygon(coords)
    >>> poly.valid
    False

    Try to fix it:

    >>> fixed = fix_invalid_geos_polygon(poly)
    >>> fixed.valid
    True
    >>> len(fixed)
    4
    >>> expected_length = 2 + 2 + 2 + 2 + 4 * math.sqrt(2)
    >>> abs(fixed.length - expected_length) < 0.000001
    True
    """

    cutoff = 0.01
    original_length = geos_polygon.length

    for method, fix_function in (
            ('buffer', fix_with_buffer),
            ('exterior', fix_with_exterior_union_polygonize)):
        if method in methods:
            fixed = fix_function(geos_polygon)
            if not fixed:
                continue
            difference = abs(original_length - fixed.length)
            if (difference / float(original_length)) < cutoff:
                return fixed
    return None


def fix_invalid_geos_multipolygon(geos_multipolygon):
    """Try to fix an invalid GEOS MultiPolygon

    Two overlapping valid polyons should be unioned to one shape:

    3  ---------                3  ---------
       | A     |                   | C     |
    2  |   ----|----            2  |       -----
       |   |   |   |   --->        |           |
    1  ----|----   |            1  -----       |
           |     B |                   |       |
    0      ---------            0      ---------

       0   1   2   3               0   1   2   3

    >>> coords_a = [(0, 1), (0, 3), (2, 3), (2, 1), (0, 1)]
    >>> coords_b = [(1, 0), (1, 2), (3, 2), (3, 0), (1, 0)]
    >>> coords_c = [(0, 1), (0, 3), (2, 3), (2, 2), (3, 2),
    ...             (3, 0), (1, 0), (1, 1), (0, 1)]

    >>> from django.contrib.gis.geos import Polygon
    >>> mp = MultiPolygon(Polygon(coords_a), Polygon(coords_b))
    >>> mp.valid
    False

    >>> fixed_mp = fix_invalid_geos_multipolygon(mp)
    >>> fixed_mp.valid
    True
    >>> expected_polygon = Polygon(coords_c)
    >>> fixed_mp.equals(expected_polygon)
    True

    If there's one valid and one fixable invalid polygon in the
    multipolygon, it should return a multipolygon with the valid one
    and the fixed version:

      2         -->--
               | D   |
               |     |
      1   --<-----<--       -----
         |     |           | E   |
         |     |           |     |
      0   -->--             -----

         0     1     2     3     4

    >>> coords_d = [(0, 0), (1, 0), (1, 2), (2, 2),
    ...             (2, 1), (0, 1), (0, 0)]
    >>> coords_e = [(3, 0), (3, 1), (4, 1), (4, 0), (3, 0)]
    >>> mp = MultiPolygon(Polygon(coords_d), Polygon(coords_e))
    >>> mp.valid
    False

    >>> fixed_mp = fix_invalid_geos_multipolygon(mp)
    >>> fixed_mp.valid
    True

    The eventual result should be three squares:

    >>> fixed_mp.num_geom
    3
    >>> fixed_mp.area
    3.0
    >>> expected_polygon = MultiPolygon(Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]),
    ...                                 Polygon([(1, 1), (1, 2), (2, 2), (2, 1), (1, 1)]),
    ...                                 Polygon([(3, 0), (3, 1), (4, 1), (4, 0), (3, 0)]))
    >>> fixed_mp.equals(expected_polygon)
    True

    If all the polygons are invalid and unfixable, an empty
    MultiPolygon will be returned.  This example, where the loop
    around the inner diamond is traversed clockwise as well, seems to
    be unfixable, so it's a good example for this:

      2  ---x---
         | / \ |
         |/   \|
      1  x     x
         |\   /|
         | \ / |
      0  ---x---

         0  1  2

    Here the points start at the bottom 'x', go right around the
    outside square clockwise and then go around the inside square
    clockwise as well.

    >>> coords = [(1, 0), (0, 0), (0, 2), (2, 2), (2, 0), (1, 0),
    ...           (0, 1), (1, 2), (2, 1), (1, 0)]
    >>> poly = Polygon(coords)
    >>> poly.valid
    False
    >>> mp = MultiPolygon(poly)
    >>> fixed = fix_invalid_geos_multipolygon(mp)
    >>> len(fixed)
    0

    """

    polygons = list(geos_multipolygon)
    # If all of the polygons in the KML are individually
    # valid, then we just need to union them:
    individually_all_valid = all(p.valid for p in polygons)
    if individually_all_valid:
        for_union = geos_multipolygon
    # Otherwise, try to fix the individually broken
    # polygons, discard any unfixable ones, and union
    # the result:
    else:
        valid_polygons = []
        for p in polygons:
            if p.valid:
                valid_polygons.append(p)
            else:
                fixed = fix_invalid_geos_polygon(p)
                if fixed is not None:
                    if fixed.geom_type == 'MultiPolygon':
                        valid_polygons += list(fixed)
                    elif fixed.geom_type == 'Polygon':
                        valid_polygons.append(fixed)
                    else:
                        raise Exception("Unknown fixed geometry type: " + fixed.geom_type)
        for_union = MultiPolygon(valid_polygons)
    if len(for_union) > 0:
        result = for_union.cascaded_union
        # If they have been unioned into a single Polygon, still return
        # a MultiPolygon, for consistency of return types:
        if result.geom_type == 'Polygon':
            result = MultiPolygon(result)
    else:
        result = for_union
    return result


def fix_invalid_geos_geometry(geos_geometry):
    """
    Try to fix a geometry if it is either a polygon or multipolygon.
    """
    if geos_geometry.geom_type == 'Polygon':
        return fix_invalid_geos_polygon(geos_geometry)
    elif geos_geometry.geom_type == 'MultiPolygon':
        return fix_invalid_geos_multipolygon(geos_geometry)
    else:
        raise Exception("Don't know how to fix an invalid %s" % geos_geometry.geom_type)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
