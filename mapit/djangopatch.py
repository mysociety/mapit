import django


def patch_set_3d():
    from django.contrib.gis.gdal import OGRGeometry

    def set_3d(self, value):
        """Set if this geometry has Z coordinates."""
        if value is True:
            self.coord_dim = 3
        elif value is False:
            self.coord_dim = 2
        else:
            raise ValueError(f"Input to 'set_3d' must be a boolean, got '{value!r}'.")

    OGRGeometry.set_3d = set_3d


if django.get_version() < '5.1':
    patch_set_3d()
