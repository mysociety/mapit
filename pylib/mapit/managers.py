from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist

def update_or_create(self, filter_attrs, attrs):
    try:
        obj = self.get(**filter_attrs)
        changed = False
        for k, v in attrs.items():
            if obj.__dict__[k] != v:
                changed = True
                obj.__dict__[k] = v
        if changed:
            obj.save()
    except ObjectDoesNotExist:
        attrs.update(filter_attrs)
        self.create(**attrs)

class GeoManager(models.GeoManager):
    def update_or_create(self, filter_attrs, attrs):
        update_or_create(self, filter_attrs, attrs)

class Manager(models.Manager):
    def update_or_create(self, filter_attrs, attrs):
        update_or_create(self, filter_attrs, attrs)

