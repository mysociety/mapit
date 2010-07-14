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

# Other possibilities for update_or_create include things like:
#
# try:
#     all = attrs.copy()
#     all.update(filter_attrs)
#     self.create(**all)
# except django.db.IntegrityError:
#     self.filter(**filter_attrs).update(**attrs)

# OR

# already = self.filter(**filter_attrs):
# if already:
#     already.update(**attrs)
# else:
#     attrs.update(filter_attrs)
#     self.create(**attrs)
