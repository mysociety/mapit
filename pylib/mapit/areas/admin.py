from django.contrib.gis import admin
from models import Area, Code, Name, Generation, Geometry

class NameInline(admin.TabularInline):
    model = Name

class CodeInline(admin.TabularInline):
    model = Code

class AreaAdmin(admin.OSMGeoAdmin):
    list_filter = ('type', 'country')
    list_display = ('name', 'type', 'country', 'generation_low', 'generation_high', 'parent_area')
    search_fields = ('names__name',)
    raw_id_fields = ('parent_area',)
    inlines = [
        NameInline,
        CodeInline,
    ]

class GeometryAdmin(admin.OSMGeoAdmin):
    raw_id_fields = ('area',)

admin.site.register(Area, AreaAdmin)
admin.site.register(Geometry, GeometryAdmin)
admin.site.register(Generation, admin.OSMGeoAdmin)
