import sys

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
            print p.geom_name
            if p.geom_name == 'POLYGON':
                shapes = [ p ]
            else:
                shapes = p
            for g in shapes:
                m.polygons.create(polygon=g.wkt)
        #m.polygon = g.wkt
        #m.save()
        poly[:] = [] # Clear the polygon's list, so that if it has both an ons_code and unit_id, it's not processed twice
    print ""

