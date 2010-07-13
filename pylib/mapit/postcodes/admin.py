from django.contrib.gis import admin
from models import Postcode

class AreaInline(admin.TabularInline):
    model = Postcode.areas.through

class PostcodeAdmin(admin.OSMGeoAdmin):
    search_fields = ['postcode']
    inlines = [
        AreaInline,
    ]
    exclude = ('areas',)

admin.site.register(Postcode, PostcodeAdmin)

