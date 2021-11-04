from __future__ import unicode_literals

from six import python_2_unicode_compatible
from django.contrib.gis.db import models


@python_2_unicode_compatible
class UPRN(models.Model):
    uprn = models.CharField(max_length=12, db_index=True, unique=True)
    postcode = models.CharField(max_length=7, db_index=True)
    location = models.PointField()

    class Meta:
        ordering = ("uprn",)

    def __str__(self):
        return self.uprn
