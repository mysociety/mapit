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

