#!/usr/bin/env python

import os
import sys
import csv
import math
import errno
import re
import json
from collections import defaultdict

import numpy as np
from matplotlib.delaunay import delaunay

from django.contrib.gis.geos import Polygon
from django.contrib.gis.gdal import DataSource

# Read all the postcode data:

script_directory = os.path.dirname(os.path.abspath(__file__))

data_directory = os.path.realpath(os.path.join(script_directory,
                                               '..',
                                               'data',
                                               'Code-Point-Open',
                                               'Data'))

output_directory = os.path.realpath(os.path.join(script_directory,
                                                 '..',
                                                 'data',
                                                 'cache',
                                                 'postcode-kml'))

# ------------------------------------------------------------------------

# Get the geometry of the UK from OpenStreetMap, so that we can
# restrict the regions at the edges of the diagram:

uk_boundary_filename = os.path.realpath(os.path.join(script_directory,
                                                     '..',
                                                     'data',
                                                     'relation-62149-United Kingdom.kml'))

uk_ds = DataSource(uk_boundary_filename)

if len(uk_ds) != 1:
    raise Exception, "Expected the UK border to only have one layer"

uk_layer = uk_ds[0]
uk_geometries = uk_layer.get_geoms(geos=True)

if len(uk_geometries) != 1:
    raise Exception, "Expected the UK layer to only have one MultiPolygon"

uk_multipolygon = uk_geometries[0]

# ------------------------------------------------------------------------

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

mkdir_p(output_directory)

# A modified version of one of the regular expressions suggested here:
#    http://en.wikipedia.org/wiki/Postcodes_in_the_United_Kingdom

postcode_matcher = re.compile(r'^([A-PR-UWYZ]([0-9][0-9A-HJKPS-UW]?|[A-HK-Y][0-9][0-9ABEHMNPRV-Y]?)) ?([0-9][ABD-HJLNP-UW-Z]{2})$')

e_sum = 0
n_sum = 0

e_min = sys.maxint
n_min = sys.maxint

e_max = -sys.maxint - 1
n_max = -sys.maxint - 1

x = np.array([])
y = np.array([])

position_to_postcodes = defaultdict(set)

total_postcodes = 0

for e in os.listdir(data_directory):
    # if e != "sw.csv":
    if e != "ab.csv":
        continue
    csv_path = os.path.join(data_directory, e)
    with open(csv_path) as fp:
        area_postcodes = len(fp.readlines())
    total_postcodes += area_postcodes
    with open(csv_path) as fp:
        reader = csv.reader(fp)
        for i, row in enumerate(reader):
            if i > 0 and (i % 1000 == 0):
                print "%s %d%%" % (e, int((100 * i) / float(area_postcodes)))
            pc = row[0]
            m = postcode_matcher.search(pc)
            if not m:
                raise Exception, "Couldn't parse postcode:", pc
            # Normalize the postcode's format to put a space in the
            # right place:
            pc = m.group(1) + " " + m.group(3)
            eastings, northings = row[2:4]
            eastings = int(eastings, 10)
            northings = int(northings, 10)
            e_min = min(e_min, eastings)
            n_min = min(n_min, eastings)
            e_max = max(n_max, northings)
            n_max = max(n_max, northings)
            e_sum += eastings
            n_sum += northings
            position_tuple = (eastings, northings)
            position_to_postcodes[position_tuple].add(pc)
            if len(position_to_postcodes[position_tuple]) == 1:
                x = np.append(x, eastings)
                y = np.append(y, northings)

centroid_x = e_sum / len(x)
centroid_y = n_sum / len(y)

# Now add some "points at infinity" - 200 points in a circle way
# outside the border of the United Kingdom:

first_infinity_index = len(x)

points_at_infinity = 200

distance_to_infinity = (n_max - n_min) * 2

for i in range(0, points_at_infinity):
    angle = (2 * math.pi * i) / float(points_at_infinity)
    x = np.append(x, centroid_x + math.cos(angle) * distance_to_infinity)
    y = np.append(y, centroid_y + math.sin(angle) * distance_to_infinity)

print "Calculating the Delaunay Triangulation..."

ccs, edges, triangles, neighbours = delaunay(x, y)

point_to_triangles = [[] for _ in x]

for i, triangle in enumerate(triangles):
    for point_index in triangle:
        point_to_triangles[point_index].append(i)

# Now generating KML:

for point_index, triangle_indices in enumerate(point_to_triangles):

    if point_index > 0 and (point_index % 100 == 0):
        print "%d%%" % (int((100 * point_index) / float(total_postcodes)),)

    centre_x = x[point_index]
    centre_y = y[point_index]
    position_tuple = centre_x, centre_y

    if len(triangle_indices) < 3:
        print "Skipping a point with fewer than 3 triangle_indices:", position_tuple
        continue

    if position_tuple not in position_to_postcodes:
        print "The position tuple had no postcodes - must be a 'point at infinity'"
        continue

    postcodes = position_to_postcodes[position_tuple]

    basename = sorted(postcodes)[0]

    # Find if any neighbouring point in the triangulation was a 'point
    # at infinity':

    requires_clipping = True

#    requires_clipping = False
#
#    for triangle_index in triangle_indices:
#        for point_index in triangles[triangle_index]:
#            if point_index >= first_infinity_index:
#                requires_clipping = True
#                break
#        if requires_clipping:
#            break

    def compare_points(a, b):
        ax = a[0] - centre_x
        ay = a[1] - centre_y
        bx = b[0] - centre_x
        by = b[1] - centre_y
        angle_a = math.atan2(ay, ax)
        angle_b = math.atan2(by, bx)
        result = angle_b - angle_a
        if result > 0:
            return 1
        elif result < 0:
            return -1
        return 0

    circumcentres = [ccs[i] for i in triangle_indices]
    sccs = np.array(sorted(circumcentres, cmp=compare_points))
    xs = [cc[0] for cc in sccs]
    ys = [cc[1] for cc in sccs]

    border = []
    for i in range(0, len(sccs) + 1):
        index_to_use = i
        if i == len(sccs):
            index_to_use = 0
        cc = (float(xs[index_to_use]),
              float(ys[index_to_use]))
        border.append(cc)

    polygon = Polygon(border, srid=27700)

    wgs_84_polygon = polygon.transform(4326, clone=True)

    if requires_clipping:
        clipped_polygon = wgs_84_polygon.intersection(uk_multipolygon)
    else:
        clipped_polygon = wgs_84_polygon

    if len(postcodes) > 1:
        json_leafname = basename + ".json"
        with open(os.path.join(output_directory, json_leafname), "w") as fp:
            json.dump(list(postcodes), fp)

    leafname = basename + ".kml"

    with open(os.path.join(output_directory, leafname), "w") as fp:
        fp.write('''<?xml version='1.0' encoding='utf-8'?>
<kml xmlns="http://earth.google.com/kml/2.1">
  <Folder>
    <name>Example KML file for testing...</name>
    <Placemark>
      %s
    </Placemark>
  </Folder>
</kml>''' % (clipped_polygon.kml,))
