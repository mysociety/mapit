import re
from django.contrib.gis.db import models

class Postcode(models.Model):
    postcode = models.CharField(max_length=7, db_index=True, unique=True)
    location = models.PointField()

    objects = models.GeoManager()

    def __unicode__(self):
        return self.get_name_display()

    def get_name_display(self):
        return re.sub('(...)$', r' \1', self.name)

