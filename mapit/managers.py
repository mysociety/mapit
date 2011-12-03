from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist

# Given unique look-up attributes, and extra data attributes,
# either updates the entry referred to if it exists, or
# creates it if it doesn't.
# Returns string describing what has happened.
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
            return 'updated'
        return 'unchanged'
    except ObjectDoesNotExist:
        attrs.update(filter_attrs)
        self.create(**attrs)
        return 'created'

class GeoManager(models.GeoManager):
    def update_or_create(self, filter_attrs, attrs):
        return update_or_create(self, filter_attrs, attrs)

class Manager(models.Manager):
    def update_or_create(self, filter_attrs, attrs):
        return update_or_create(self, filter_attrs, attrs)

