from django.conf.urls.defaults import *
from mapit.shortcuts import render

handler500 = 'mapit.shortcuts.json_500'

format_end = '(?:\.(?P<format>html|json))?'

urlpatterns = patterns('',
    (r'^$', render, { 'template_name': 'mapit/index.html' }, 'mapit_index' ),
    (r'^licensing$', render, { 'template_name': 'mapit/licensing.html' } ),
    (r'^overview$', render, { 'template_name': 'mapit/overview.html' } ),

    (r'^generations$', 'mapit.views.areas.generations'),

    (r'^postcode/$', 'mapit.views.postcodes.form_submitted'),
    (r'^postcode/(?P<postcode>[A-Za-z0-9 +]+)%s$' % format_end, 'mapit.views.postcodes.postcode'),
    (r'^postcode/partial/(?P<postcode>[A-Za-z0-9 ]+)%s$' % format_end, 'mapit.views.postcodes.partial_postcode'),

    (r'^area/(?P<area_id>[0-9A-Z]+)%s$' % format_end, 'mapit.views.areas.area'),
    (r'^area/(?P<area_id>[0-9]+)/example_postcode%s$' % format_end, 'mapit.views.postcodes.example_postcode_for_area'),
    (r'^area/(?P<area_id>[0-9]+)/children%s$' % format_end, 'mapit.views.areas.area_children'),
    (r'^area/(?P<area_id>[0-9]+)/geometry$', 'mapit.views.areas.area_geometry'),
    (r'^area/(?P<area_id>[0-9]+)/touches%s$' % format_end, 'mapit.views.areas.area_touches'),
    (r'^area/(?P<area_id>[0-9]+)/overlaps%s$' % format_end, 'mapit.views.areas.area_overlaps'),
    (r'^area/(?P<area_id>[0-9]+)/covers%s$' % format_end, 'mapit.views.areas.area_covers'),
    (r'^area/(?P<area_id>[0-9]+)/covered%s$' % format_end, 'mapit.views.areas.area_covered'),
    (r'^area/(?P<area_id>[0-9]+)/coverlaps%s$' % format_end, 'mapit.views.areas.area_coverlaps'),
    (r'^area/(?P<area_id>[0-9]+)/intersects%s$' % format_end, 'mapit.views.areas.area_intersects'),
    (r'^area/(?P<area_id>[0-9A-Z]+)\.(?P<format>kml|geojson|wkt)$', 'mapit.views.areas.area_polygon'),
    (r'^area/(?P<srid>[0-9]+)/(?P<area_id>[0-9]+)\.(?P<format>kml|json|geojson|wkt)$', 'mapit.views.areas.area_polygon'),

    (r'^point/$', 'mapit.views.areas.point_form_submitted'),
    (r'^point/(?P<srid>[0-9]+)/(?P<x>[0-9.-]+),(?P<y>[0-9.-]+)(?:/(?P<bb>box))?%s$' % format_end, 'mapit.views.areas.areas_by_point'),
    (r'^point/latlon/(?P<lat>[0-9.-]+),(?P<lon>[0-9.-]+)(?:/(?P<bb>box))?%s$' % format_end, 'mapit.views.areas.areas_by_point_latlon'),
    (r'^point/osgb/(?P<e>[0-9.-]+),(?P<n>[0-9.-]+)(?:/(?P<bb>box))?%s$' % format_end, 'mapit.views.areas.areas_by_point_osgb'),

    (r'^nearest/(?P<srid>[0-9]+)/(?P<x>[0-9.-]+),(?P<y>[0-9.-]+)%s$' % format_end, 'mapit.views.postcodes.nearest'),

    (r'^areas/(?P<area_ids>[0-9,]*[0-9]+)%s$' % format_end, 'mapit.views.areas.areas'),
    (r'^areas/(?P<area_ids>[0-9,]*[0-9]+)/geometry$', 'mapit.views.areas.areas_geometry'),
    (r'^areas/(?P<type>[A-Z0-9,]*[A-Z0-9]+)%s$' % format_end, 'mapit.views.areas.areas_by_type'),
    (r'^areas/(?P<name>.+?)%s$' % format_end, 'mapit.views.areas.areas_by_name'),
    (r'^areas$', 'mapit.views.areas.deal_with_POST', { 'call': 'areas' }),
    (r'^code/(?P<code_type>[^/]+)/(?P<code_value>[^/]+?)%s$' % format_end, 'mapit.views.areas.area_from_code'),
)
