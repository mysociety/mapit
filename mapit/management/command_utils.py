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
        #g = OGRGeometry(OGRGeomType('MultiPolygon'))
        m.polygons.all().delete()
        for p in poly:
            if p.geom_name == 'POLYGON':
                shapes = [ p ]
            else:
                shapes = p
            for g in shapes:
                # Ignore any shape with fewer than four points, to
                # avoid introducing invalid polygons into the
                # database.
                if g.point_count < 4:
                    continue
                # XXX Using g.wkt directly when importing Norway KML works fine
                # with Django 1.1, Postgres 8.3, PostGIS 1.3.3 but fails with
                # Django 1.2, Postgres 8.4, PostGIS 1.5.1, saying that the
                # dimensions constraint fails - because it is trying to import
                # a shape as 3D as the WKT contains " 0" at the end of every
                # co-ordinate. Removing the altitudes from the KML, and/or
                # using altitudeMode makes no difference to the WKT here, so
                # the only easy solution appears to be removing the altitude
                # directly from the WKT before using it.
                must_be_two_d = g.wkt.replace(' 0,', ',')
                m.polygons.create(polygon=must_be_two_d)
        #m.polygon = g.wkt
        #m.save()
        poly[:] = [] # Clear the polygon's list, so that if it has both an ons_code and unit_id, it's not processed twice
    print ""


def fix_with_buffer(geos_polygon):
    return geos_polygon.buffer(0)

def fix_with_exterior_union_polygonize(geos_polygon):
    exterior_ring = geos_polygon.exterior_ring
    unioned = exterior_ring.union(exterior_ring)
    # We want to use GEOSPolygonize which isn't exposed via
    # django.contrib.gis.geos, but is available via shapely:
    shapely_unioned = shapely.wkt.loads(unioned.wkt)
    reconstructed_geos_polygons = [
        GEOSGeometry(sp.wkt, geos_polygon.srid) for sp in
        shapely.ops.polygonize(shapely_unioned)]
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
        ('exterior', fix_with_exterior_union_polygonize)
        ):
        if method in methods:
            fixed = fix_function(geos_polygon)
            if not fixed:
                continue
            difference = abs(original_length - fixed.length)
            if (difference / float(original_length)) < cutoff:
                return fixed
    return None

if __name__ == "__main__":
    import doctest
    doctest.testmod()
