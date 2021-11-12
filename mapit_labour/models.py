from __future__ import unicode_literals

import re
from six import python_2_unicode_compatible
from django.db import connection
from django.contrib.gis.db import models

from mapit.models import str2int, Area, CodeType


@python_2_unicode_compatible
class UPRN(models.Model):
    uprn = models.CharField(max_length=12, db_index=True, unique=True)
    postcode = models.CharField(max_length=7, db_index=True)
    location = models.PointField()

    class Meta:
        ordering = ("uprn",)

    def __str__(self):
        return self.uprn

    def as_dict(self):
        (easting, northing) = self.as_uk_grid()

        return {
            "uprn": self.uprn,
            "postcode": self.postcode,
            "wgs84_lon": self.location[0],
            "wgs84_lat": self.location[1],
            "easting": easting,
            "northing": northing,
            "addressbase_core": self.addressbase_core_record,
        }

    @property
    def addressbase_core_record(self):
        # return {}
        return {c.type.code: c.code for c in self.codes.all()}

    def as_uk_grid(self):
        cursor = connection.cursor()
        srid = 27700
        cursor.execute(
            "SELECT ST_AsText(ST_Transform(ST_GeomFromText('POINT(%f %f)', 4326), %d))"
            % (self.location[0], self.location[1], srid)
        )
        row = cursor.fetchone()
        m = re.match(r"POINT\((.*?) (.*)\)", row[0])
        return list(map(str2int, m.groups()))


@python_2_unicode_compatible
class Code(models.Model):
    uprn = models.ForeignKey(UPRN, related_name="codes", on_delete=models.CASCADE)
    type = models.ForeignKey(
        CodeType, related_name="uprn_codes", on_delete=models.CASCADE
    )
    code = models.CharField(max_length=500, db_index=True)
    objects = models.Manager()

    class Meta:
        unique_together = ("uprn", "type")

    def __str__(self):
        return "%s (%s) [%s]" % (self.code, self.type.code, self.uprn.uprn)
