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

