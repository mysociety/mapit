from django.contrib.gis import admin
from models import Postcode

admin.site.register(Postcode, admin.OSMGeoAdmin)

