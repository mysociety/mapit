from django.contrib.gis import admin

from mapit_labour.models import UPRN, Code


class CodeInline(admin.TabularInline):
    model = Code


class UPRNAdmin(admin.OSMGeoAdmin):
    search_fields = ["uprn", "postcode"]
    list_display = ("uprn", "postcode")

    inlines = [
        CodeInline,
    ]


admin.site.register(UPRN, UPRNAdmin)
