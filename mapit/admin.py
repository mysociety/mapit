from django.contrib.gis import admin
from django.utils.html import format_html

from mapit.models import Area, Code, Name, Generation, Geometry, Postcode, Type, NameType, CodeType, Country


class NameInline(admin.TabularInline):
    model = Name


class CodeInline(admin.TabularInline):
    model = Code


class AreaAdmin(admin.GISModelAdmin):
    list_filter = ('type', 'country')
    list_display = ('name', 'type', 'country', 'generation_low', 'generation_high', 'parent_area', 'geometries_link')
    search_fields = ('name', 'names__name', 'codes__code')
    raw_id_fields = ('parent_area',)
    inlines = [
        NameInline,
        CodeInline,
    ]

    def geometries_link(self, obj):
        return format_html('<a href="../geometry/?area=%d">Shapes</a>' % obj.id)


class GeometryAdmin(admin.GISModelAdmin):
    raw_id_fields = ('area',)


class GenerationAdmin(admin.GISModelAdmin):
    list_display = ('id', 'active', 'created', 'description')


class PostcodeAdmin(admin.GISModelAdmin):
    search_fields = ['postcode']
    raw_id_fields = ('areas',)


class TypeAdmin(admin.GISModelAdmin):
    pass


class NameTypeAdmin(admin.GISModelAdmin):
    pass


class CodeTypeAdmin(admin.GISModelAdmin):
    pass


class CountryAdmin(admin.GISModelAdmin):
    pass


admin.site.register(Area, AreaAdmin)
admin.site.register(Geometry, GeometryAdmin)
admin.site.register(Generation, GenerationAdmin)
admin.site.register(Postcode, PostcodeAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(CodeType, CodeTypeAdmin)
admin.site.register(NameType, NameTypeAdmin)
admin.site.register(Country, CountryAdmin)
