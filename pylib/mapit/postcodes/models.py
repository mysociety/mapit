import re
from django.contrib.gis.db import models
from django.db import connection, transaction
from django.conf import settings
from mapit.managers import GeoManager
from mapit.areas.models import Area
import mapit.countries

class PostcodeManager(GeoManager):
    def get_query_set(self):
        return self.model.QuerySet(self.model)
    def __getattr__(self, attr, *args):
        return getattr(self.get_query_set(), attr, *args)

class Postcode(models.Model):
    postcode = models.CharField(max_length=7, db_index=True, unique=True)
    location = models.PointField(null=True)
    # Will hopefully use PostGIS point-in-polygon tests, but if we don't have the polygons...
    areas = models.ManyToManyField(Area, related_name='postcodes', blank=True)

    objects = PostcodeManager()

    class Meta:
        ordering = ('postcode',)

    class QuerySet(models.query.GeoQuerySet):
        # ST_CoveredBy on its own does not appear to use the index.
        # Plus this way we can keep the polygons in the database
        # without pulling out in a giant WKB string
        def filter_by_area(self, area):
            collect = 'ST_Transform((select ST_Collect(polygon) from areas_geometry where area_id=%s group by area_id), 4326)'
            return self.extra(
                where = [
                    'location && %s' % collect,
                    'ST_CoveredBy(location, %s)' % collect
                ],
                params = [ area.id, area.id ]
            )

    def __unicode__(self):
        return self.get_postcode_display()

    # Prettify postcode for display, if we know how to
    def get_postcode_display(self):
        if hasattr(mapit.countries, 'get_postcode_display'):
            return mapit.countries.get_postcode_display(self.postcode)
        return self.postcode

    def as_dict(self):
        if not self.location:
            return {
                'postcode': self.get_postcode_display(),
            }
        loc = self.location
        result = {
            'postcode': self.get_postcode_display(),
            'wgs84_lon': loc[0],
            'wgs84_lat': loc[1]
        }
        if hasattr(mapit.countries, 'augment_postcode'):
            mapit.countries.augment_postcode(self, result)
        return result

    # Doing this via self.location.transform(29902) gives incorrect results.
    # The database has the right proj4 text, the proj file does not. I think.
    def as_irish_grid(self):
        cursor = connection.cursor()
        cursor.execute("SELECT ST_AsText(ST_Transform(ST_GeomFromText('POINT(%f %f)', 4326), 29902))" % (self.location[0], self.location[1]))
        row = cursor.fetchone()
        m = re.match('POINT\((.*?) (.*)\)', row[0])
        return map(float, m.groups())

