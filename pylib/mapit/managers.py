from django.contrib.gis.db import models

class GeoManager(models.GeoManager):
    def update_or_create(self, filter_attrs, attrs):
        if not self.filter(**filter_attrs).update(**attrs):
            attrs.update(filter_attrs)
            self.create(**attrs)

class Manager(models.Manager):
    def update_or_create(self, filter_attrs, attrs):
        if not self.filter(**filter_attrs).update(**attrs):
            attrs.update(filter_attrs)
            self.create(**attrs)

