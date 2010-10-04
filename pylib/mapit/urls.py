from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

handler500 = 'mapit.shortcuts.json_500'

from django.contrib import admin
admin.autodiscover()

format_end = '(?:\.(?P<format>html|json))?'

urlpatterns = patterns('',
    (r'^$', direct_to_template, { 'template': 'index.html' }),

    (r'^generations$', 'mapit.areas.views.generations'),

    (r'^postcode/(?P<postcode>[A-Za-z0-9 +]+)%s$' % format_end, 'mapit.postcodes.views.postcode'),
    (r'^postcode/partial/(?P<postcode>[A-Za-z0-9 ]+)%s$' % format_end, 'mapit.postcodes.views.partial_postcode'),

    (r'^area/(?P<area_id>[0-9A-Z]+)%s$' % format_end, 'mapit.areas.views.area'),
    (r'^area/(?P<area_id>[0-9]+)/example_postcode%s$' % format_end, 'mapit.postcodes.views.example_postcode_for_area'),
    (r'^area/(?P<area_id>[0-9]+)/children%s$' % format_end, 'mapit.areas.views.area_children'),
    (r'^area/(?P<area_id>[0-9]+)/geometry$', 'mapit.areas.views.area_geometry'),
    (r'^area/(?P<area_id>[0-9]+)/touches%s$' % format_end, 'mapit.areas.views.area_touches'),
    (r'^area/(?P<area_id>[0-9]+)/overlaps%s$' % format_end, 'mapit.areas.views.area_overlaps'),
    (r'^area/(?P<area_id>[0-9]+)/covers%s$' % format_end, 'mapit.areas.views.area_covers'),
    (r'^area/(?P<area_id>[0-9]+)/covered%s$' % format_end, 'mapit.areas.views.area_covered'),
    (r'^area/(?P<area_id>[0-9]+)\.(?P<format>kml|json|wkt)$', 'mapit.areas.views.area_polygon'),
    (r'^area/(?P<srid>[0-9]+)/(?P<area_id>[0-9]+)\.(?P<format>kml|json|wkt)$', 'mapit.areas.views.area_polygon'),

    (r'^point/(?P<srid>[0-9]+)/(?P<x>[0-9.-]+),(?P<y>[0-9.-]+)(?:/(?P<bb>box))?%s$' % format_end, 'mapit.areas.views.areas_by_point'),
    (r'^point/latlon/(?P<lat>[0-9.-]+),(?P<lon>[0-9.-]+)(?:/(?P<bb>box))?%s$' % format_end, 'mapit.areas.views.areas_by_point_latlon'),
    (r'^point/osgb/(?P<e>[0-9.-]+),(?P<n>[0-9.-]+)(?:/(?P<bb>box))?%s$' % format_end, 'mapit.areas.views.areas_by_point_osgb'),

    (r'^areas/(?P<area_ids>[0-9,]*[0-9]+)%s$' % format_end, 'mapit.areas.views.areas'),
    (r'^areas/(?P<area_ids>[0-9,]*[0-9]+)/geometry$', 'mapit.areas.views.areas_geometry'),
    (r'^areas/(?P<type>[A-Z,]*[A-Z]+)%s$' % format_end, 'mapit.areas.views.areas_by_type'),
    (r'^areas/(?P<name>.+?)%s$' % format_end, 'mapit.areas.views.areas_by_name'),
    (r'^areas$', 'mapit.areas.views.deal_with_POST', { 'call': 'areas' }),

    (r'^admin/', include(admin.site.urls)),

    # Old style MaPit calls
    (r'^get_voting_areas/([A-Za-z0-9 ]+)$', 'mapit.postcodes.views.postcode', { 'legacy': True }),
    (r'^get_voting_area_info/([0-9A-Za-z]+)$', 'mapit.areas.views.get_voting_area_info'),
    (r'^get_voting_areas_info/(?P<area_ids>[0-9A-Za-z,]+)$', 'mapit.areas.views.get_voting_areas_info'),
    (r'^get_voting_areas_info$', 'mapit.areas.views.deal_with_POST', { 'call': 'get_voting_areas_info' }),
    (r"^get_voting_area_by_name/(.+?)$", 'mapit.areas.views.areas_by_name', { 'legacy': True }),
    (r'^get_areas_by_type/([A-Z,]+)$', 'mapit.areas.views.areas_by_type', { 'legacy': True }),
    (r'^get_voting_area_geometry/([0-9]+)$', 'mapit.areas.views.area_geometry', { 'legacy': True }),
    (r'^get_voting_areas_geometry/([0-9,]+)$', 'mapit.areas.views.areas_geometry', { 'legacy': True }),
    (r'^get_voting_areas_by_location/(?P<srid>27700|4326)/(?P<x>[0-9.-]+),(?P<y>[0-9.-]+)/(?P<bb>box|polygon)$', 'mapit.areas.views.areas_by_point', { 'legacy': True }),
    (r'^get_example_postcode/([0-9]+)$', 'mapit.postcodes.views.example_postcode_for_area', { 'legacy': True }),
    (r'^get_voting_area_children/([0-9]+)$', 'mapit.areas.views.area_children', { 'legacy': True }),
    (r'^get_location/([A-Za-z0-9 ]+)(?:/(partial))?$', 'mapit.postcodes.views.get_location'),
)
