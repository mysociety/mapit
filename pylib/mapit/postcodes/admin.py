from django.contrib.gis import admin
from models import Postcode

class PostcodeAdmin(admin.OSMGeoAdmin):
    search_fields = ['postcode']

admin.site.register(Postcode, PostcodeAdmin)

