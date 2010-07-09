from django.contrib.gis import admin
from models import Area

admin.site.register(Area, admin.OSMGeoAdmin)

