# From https://gist.github.com/bpartridge/26a11b28415d706bfb9993fc28767d68

import django


def patch_geos_signatures():
    """
    Patch GEOS to function on macOS arm64 and presumably
    other odd architectures by ensuring that call signatures
    are explicit, and that Django 4 bugfixes are backported.

    Should work on Django 2.2+, minimally tested, caveat emptor.
    """
    import logging

    from ctypes import POINTER, c_uint, c_int
    from django.contrib.gis.geos import GeometryCollection, Polygon
    from django.contrib.gis.geos import prototypes as capi
    from django.contrib.gis.geos.prototypes import GEOM_PTR
    from django.contrib.gis.geos.prototypes.geom import GeomOutput
    from django.contrib.gis.geos.libgeos import geos_version, lgeos
    from django.contrib.gis.geos.linestring import LineString

    logger = logging.getLogger("geos_patch")

    _geos_version = geos_version()
    logger.debug("GEOS: %s %s", _geos_version, repr(lgeos))

    # Backport https://code.djangoproject.com/ticket/30274
    def new_linestring_iter(self):
        for i in range(len(self)):
            yield self[i]

    LineString.__iter__ = new_linestring_iter

    # macOS arm64 requires that we have explicit argtypes for cffi calls.
    # Patch in argtypes for `create_polygon` and `create_collection`,
    # and then ensure their prep functions do NOT use byref so that the
    # arrays (`(GEOM_PTR * length)(...)`) auto-convert into `Geometry**`.
    # create_empty_polygon doesn't need to be patched as it takes no args.

    # Geometry*
    # GEOSGeom_createPolygon_r(GEOSContextHandle_t extHandle,
    #   Geometry* shell, Geometry** holes, unsigned int nholes)
    capi.create_polygon = GeomOutput(
        "GEOSGeom_createPolygon", argtypes=[GEOM_PTR, POINTER(GEOM_PTR), c_uint]
    )

    # Geometry*
    # GEOSGeom_createCollection_r(GEOSContextHandle_t extHandle,
    #   int type, Geometry** geoms, unsigned int ngeoms)
    capi.create_collection = GeomOutput(
        "GEOSGeom_createCollection", argtypes=[c_int, POINTER(GEOM_PTR), c_uint]
    )

    # The below implementations are taken directly from Django 2.2.25 source;
    # the only changes are unwrapping calls to byref().

    def new_create_polygon(self, length, items):
        # Instantiate LinearRing objects if necessary, but don't clone them yet
        # _construct_ring will throw a TypeError if a parameter isn't a valid ring
        # If we cloned the pointers here, we wouldn't be able to clean up
        # in case of error.
        if not length:
            return capi.create_empty_polygon()

        rings = []
        for r in items:
            if isinstance(r, GEOM_PTR):
                rings.append(r)
            else:
                rings.append(self._construct_ring(r))

        shell = self._clone(rings.pop(0))

        n_holes = length - 1
        if n_holes:
            holes = (GEOM_PTR * n_holes)(*[self._clone(r) for r in rings])
            holes_param = holes
        else:
            holes_param = None

        return capi.create_polygon(shell, holes_param, c_uint(n_holes))

    Polygon._create_polygon = new_create_polygon

    # Need to patch to not call byref so that we can cast to a pointer
    def new_create_collection(self, length, items):
        # Creating the geometry pointer array.
        geoms = (GEOM_PTR * length)(
            *[
                # this is a little sloppy, but makes life easier
                # allow GEOSGeometry types (python wrappers) or pointer types
                capi.geom_clone(getattr(g, "ptr", g))
                for g in items
            ]
        )
        return capi.create_collection(c_int(self._typeid), geoms, c_uint(length))

    GeometryCollection._create_collection = new_create_collection


if django.get_version() < '4.0.1':
    patch_geos_signatures()
