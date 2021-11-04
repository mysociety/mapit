from django.contrib.gis import admin

from mapit_labour.models import UPRN


class UPRNAdmin(admin.OSMGeoAdmin):
    search_fields = ["uprn", "postcode"]
    list_display = ("uprn", "postcode")


admin.site.register(UPRN, UPRNAdmin)
