from django.contrib.gis import admin
from models import Area, Code, Name, Generation, Geometry

class NameInline(admin.TabularInline):
    model = Name

class CodeInline(admin.TabularInline):
    model = Code

class AreaAdmin(admin.OSMGeoAdmin):
    list_filter = ('type', 'country')
    list_display = ('name', 'type', 'country', 'generation_low', 'generation_high', 'parent_area', 'geometries_link')
    search_fields = ('names__name',)
    raw_id_fields = ('parent_area',)
    inlines = [
        NameInline,
        CodeInline,
    ]

    def geometries_link(self, obj):
        return '<a href="../geometry/?area=%d">Shapes</a>' % obj.id
    geometries_link.allow_tags = True

class GeometryAdmin(admin.OSMGeoAdmin):
    raw_id_fields = ('area',)

class GenerationAdmin(admin.OSMGeoAdmin):
    list_display = ('id', 'active', 'created', 'description')

admin.site.register(Area, AreaAdmin)
admin.site.register(Geometry, GeometryAdmin)
admin.site.register(Generation, GenerationAdmin)
