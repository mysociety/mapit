from django.contrib.gis import admin
from models import Area, Code, Name, Generation

class NameInline(admin.TabularInline):
    model = Name

class CodeInline(admin.TabularInline):
    model = Code

class AreaAdmin(admin.OSMGeoAdmin):
    inlines = [
        NameInline,
        CodeInline,
    ]

admin.site.register(Area, AreaAdmin)
admin.site.register(Generation, admin.OSMGeoAdmin)
