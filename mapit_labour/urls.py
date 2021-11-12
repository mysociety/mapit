from django.conf.urls import url

from mapit_labour.views import uprn, addressbase


format_end = r"(?:\.(?P<format>html|json))?"

urlpatterns = [
    url(r"^uprn/(?P<uprn>[0-9]+)%s$" % format_end, uprn, name="mapit_labour-uprn"),
    url(r"^addressbase$", addressbase, name="mapit_labour-addressbase"),
]
