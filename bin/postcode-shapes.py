#!/usr/bin/env python

from collections import defaultdict
import math

# Example from: http://glowingpython.blogspot.co.uk/2011/05/delaunay-triangulation-with-matplotlib.html

from matplotlib.delaunay import delaunay
import matplotlib.pyplot as plt
import numpy
from matplotlib.patches import Polygon

# 4 random points (x,y) in the plane

# x = numpy.array([-10, -8, 9, 0, -7])
# y = numpy.array([-8, 7, -4, -2, -1])

x,y = numpy.array(numpy.random.standard_normal((2, 40)))

points_at_infinity = 30
distance_to_infinity = 50

for i in range(0, points_at_infinity):
    angle = (2 * math.pi * i) / float(points_at_infinity)
    x = numpy.append(x, math.cos(angle) * distance_to_infinity)
    y = numpy.append(y, math.sin(angle) * distance_to_infinity)

ccs, edges, triangles, neighbours = delaunay(x, y)

point_to_triangles = [[] for _ in x]

for i, triangle in enumerate(triangles):
    for point_index in triangle:
        point_to_triangles[point_index].append(i)

# for t in triangles:
#     # t[0], t[1], t[2] are the points indexes of the triangle
#     t_i = [t[0], t[1], t[2], t[0]]
#    plt.plot(x[t_i], y[t_i])

plt.plot(x, y, 'ro')

import math

for point_index, triangle_indices in enumerate(point_to_triangles):
    centre_x = x[point_index]
    centre_y = y[point_index]
    def compare_points(a, b):
        ax = a[0] - centre_x
        ay = a[1] - centre_y
        bx = b[0] - centre_x
        by = b[1] - centre_y
        # result = ay * bx - ax * by
        angle_a = math.atan2(ay, ax)
        angle_b = math.atan2(by, bx)
        result = angle_b - angle_a
        if result > 0:
            return 1
        elif result < 0:
            return -1
        return 0

    circumcentres = [ccs[i] for i in triangle_indices]
    sccs = numpy.array(sorted(circumcentres, cmp=compare_points))
    # xy = numpy.array(ccs[i] for i in triangle_indices)
    xs = [cc[0] for cc in sccs]
    ys = [cc[1] for cc in sccs]
    # polygon = Polygon(xy)
    # print "created polygon:", polygon
    # plt.fill(polygon)
    # plt.plot(xs, ys)
    plt.fill(xs, ys, closed=True)
    plt.plot(x[point_index], y[point_index], 'yo')

plt.show()
