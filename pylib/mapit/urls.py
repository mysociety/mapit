from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', direct_to_template, { 'template': 'index.html' }),

    (r'^postcode/(?P<postcode>[A-Za-z0-9 ]+)$', 'mapit.postcodes.views.postcode'),
    (r'^postcode/partial/(?P<postcode>[A-Za-z0-9 ]+)$', 'mapit.postcodes.views.partial_postcode'),

    (r'^area/(?P<area_id>[0-9]+)$', 'mapit.areas.views.area'),
    (r'^area/(?P<area_id>[0-9]+)/example_postcode$', 'mapit.postcode.views.example_postcode_for_area'),
    (r'^area/(?P<area_id>[0-9]+)/children$', 'mapit.areas.views.area_children'),
    (r'^area/(?P<area_id>[0-9]+)/geometry$', 'mapit.areas.views.area_geometry'),
    (r'^area/(?P<area_id>[0-9]+)\.(?P<format>kml|json|wkt)$', 'mapit.areas.views.area_polygon'),

    (r'^point/(?P<srid>[0-9]+)/(?P<x>[0-9.-]+),(?P<y>[0-9.-]+)(?:/(?P<bb>box))?$', 'mapit.areas.views.areas_by_point'),

    (r'^areas/(?P<area_ids>[0-9,]+)$', 'mapit.areas.views.areas'),
    (r'^areas/(?P<name>.+?)$', 'mapit.areas.views.areas_by_name'),
    (r'^areas/(?P<type>[A-Z,]+)$', 'mapit.areas.views.areas_by_type'),

    (r'^admin/', include(admin.site.urls)),

    # Old style MaPit calls
    (r'^get_voting_areas/([A-Za-z0-9 ]+)$', 'mapit.postcodes.views.get_voting_areas'),
    (r'^get_voting_area_info/([0-9]+)$', 'mapit.areas.views.get_voting_area_info'),
    (r'^get_voting_areas_info/([0-9,]+)$', 'mapit.areas.views.get_voting_areas_info'),
    (r"^get_voting_area_by_name/(.+?)$", 'mapit.areas.views.get_voting_area_by_name'),
    (r'^get_areas_by_type/([A-Z,]+)$', 'mapit.areas.views.get_areas_by_type'),
    (r'^get_voting_area_geometry/([0-9]+)(?:/(polygon))?$', 'mapit.areas.views.get_voting_area_geometry'),
    (r'^get_voting_areas_geometry/([0-9,]+)(?:/(polygon))?$', 'mapit.areas.views.get_voting_areas_geometry'),
    (r'^get_voting_areas_by_location/(osgb|wgs84)/([0-9.-]+),([0-9.-]+)/(box|polygon)$', 'mapit.areas.views.get_voting_areas_by_location'),
    (r'^get_example_postcode/([0-9]+)$', 'mapit.postcodes.views.get_example_postcode'),
    (r'^get_voting_area_children/([0-9]+)$', 'mapit.areas.views.area_children', { 'legacy': True }),
    (r'^get_location/([A-Za-z0-9 ]+)(?:/(partial))?$', 'mapit.postcodes.views.get_location'),
)
