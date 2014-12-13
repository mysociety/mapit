import sys

import django
from django.contrib.gis.db import models
from django.db import IntegrityError
from django.utils import six

try:
    # Django 1.5+
    from django.db.models.constants import LOOKUP_SEP
except ImportError:
    # Django <= 1.4
    from django.db.models.sql.constants import LOOKUP_SEP


# A copy of Django 1.7's built-in function, except for the 1.6+ transaction
# aspects. And with create() used instead of self.model() & obj.save(), as in
# older versions that passes the related ID in correctly.

def _create_object_from_params(self, lookup, params):
    """
    Tries to create an object using passed params.
    Used by get_or_create and update_or_create
    """
    try:
        obj = self.create(**params)
        return obj, True
    except IntegrityError:
        exc_info = sys.exc_info()
        try:
            return self.get(**lookup), False
        except self.model.DoesNotExist:
            pass
        six.reraise(*exc_info)


def _extract_model_params(self, defaults, **kwargs):
    """
    Prepares `lookup` (kwargs that are valid model attributes), `params`
    (for creating a model instance) based on given kwargs; for use by
    get_or_create and update_or_create.
    """
    defaults = defaults or {}
    lookup = kwargs.copy()
    for f in self.model._meta.fields:
        if f.attname in lookup:
            lookup[f.name] = lookup.pop(f.attname)
    params = dict((k, v) for k, v in kwargs.items() if LOOKUP_SEP not in k)
    params.update(defaults)
    return lookup, params


def update_or_create(self, defaults=None, **kwargs):
    """
    Looks up an object with the given kwargs, updating one with defaults
    if it exists, otherwise creates a new one.
    Returns a tuple (object, created), where created is a boolean
    specifying whether an object was created.
    """
    defaults = defaults or {}
    lookup, params = _extract_model_params(self, defaults, **kwargs)
    self._for_write = True
    try:
        obj = self.get(**lookup)
    except self.model.DoesNotExist:
        obj, created = _create_object_from_params(self, lookup, params)
        if created:
            return obj, created
    for k, v in six.iteritems(defaults):
        setattr(obj, k, v)

    obj.save(using=self.db)
    return obj, False


# Django 1.7 added a built-in update_or_create function.
if django.VERSION < (1, 7):
    class GeoManager(models.GeoManager):
        def update_or_create(self, defaults=None, **lookup):
            return update_or_create(self, defaults, **lookup)

    class Manager(models.Manager):
        def update_or_create(self, defaults=None, **lookup):
            return update_or_create(self, defaults, **lookup)

else:

    class GeoManager(models.GeoManager):
        pass

    class Manager(models.Manager):
        pass
