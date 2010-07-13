from django.contrib.gis import admin
from models import Postcode

class PostcodeAdmin(admin.OSMGeoAdmin):
    search_fields = ['postcode']
    raw_id_fields = ('areas',)

admin.site.register(Postcode, PostcodeAdmin)

