import re
from django.contrib.gis.db import models
from mapit.managers import GeoManager
from mapit.areas.models import Area

class Postcode(models.Model):
    postcode = models.CharField(max_length=7, db_index=True, unique=True)
    location = models.PointField()
    # Will hopefully use PostGIS point-in-polygon tests, but if we don't have the polygons...
    areas = models.ManyToManyField(Area, related_name='postcodes')

    objects = GeoManager()

    class Meta:
        ordering = ('postcode',)

    def __unicode__(self):
        return self.get_postcode_display()

    def get_postcode_display(self):
        return re.sub('(...)$', r' \1', self.postcode)

    def as_dict(self):
        loc = self.location
        result = {}
        result['postcode'] = self.get_postcode_display()
        result['wgs84_lon'] = loc[0]
        result['wgs84_lat'] = loc[1]
        if self.postcode[0:2] == 'BT':
            loc.transform(29902)
            result['coordsyst'] = 'I'
        else:
            loc.transform(27700)
            result['coordsyst'] = 'G'
        result['easting'] = int(round(loc[0]))
        result['northing'] = int(round(loc[1]))
        return result

