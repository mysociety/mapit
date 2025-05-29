from django.urls import include, re_path
from django.conf import settings
from django.shortcuts import render

from mapit.utils import re_number as number
from mapit.views import areas, postcodes

handler500 = 'mapit.shortcuts.json_500'

format_end = r'(?:\.(?P<format>html|json))?'
map_format_end = r'(?:\.(?P<format>map\.html|html|json))?'
data_format_end = r'\.(?P<format>kml|geojson)'

urlpatterns = [
    re_path(r'^$', render, {'template_name': 'mapit/index.html'}, 'mapit_index'),
    re_path(r'^licensing$', render, {'template_name': 'mapit/licensing.html'}),
    re_path(r'^overview$', render, {'template_name': 'mapit/overview.html'}),

    re_path(r'^generations%s$' % format_end, areas.generations, {}, 'mapit_generations'),

    re_path(r'^postcode/$', postcodes.form_submitted),
    re_path(r'^postcode/(?P<postcode>[A-Za-z0-9 +]+)%s$' % format_end, postcodes.postcode, name="mapit-postcode"),
    re_path(r'^postcode/partial/(?P<postcode>[A-Za-z0-9 ]+)%s$' % format_end,
            postcodes.partial_postcode, name="mapit-postcode-partial"),

    re_path(r'^area/(?P<area_id>[0-9A-Z]+)%s$' % format_end, areas.area, name='area'),
    re_path(r'^area/(?P<area_id>[0-9]+)/example_postcode%s$' % format_end, postcodes.example_postcode_for_area),
    re_path(r'^area/(?P<area_id>[0-9]+)/children%s$' % map_format_end, areas.area_children),
    re_path(r'^area/(?P<area_id>[0-9]+)/children%s$' % data_format_end, areas.area_children),
    re_path(r'^area/(?P<area_id>[0-9]+)/geometry$', areas.area_geometry),
    re_path(r'^area/(?P<area_id>[0-9]+)/touches%s$' % map_format_end, areas.area_touches),
    re_path(r'^area/(?P<area_id>[0-9]+)/overlaps%s$' % map_format_end, areas.area_overlaps),
    re_path(r'^area/(?P<area_id>[0-9]+)/covers%s$' % map_format_end, areas.area_covers),
    re_path(r'^area/(?P<area_id>[0-9]+)/covered%s$' % map_format_end, areas.area_covered),
    re_path(r'^area/(?P<area_id>[0-9]+)/coverlaps%s$' % map_format_end, areas.area_coverlaps),
    re_path(r'^area/(?P<area_id>[0-9]+)/intersects%s$' % map_format_end, areas.area_intersects),
    re_path(r'^area/(?P<area_id>[0-9A-Z]+)\.(?P<format>kml|geojson|wkt)$', areas.area_polygon, name='area_polygon'),
    re_path(r'^area/(?P<srid>[0-9]+)/(?P<area_id>[0-9]+)\.(?P<format>kml|json|geojson|wkt)$',
            areas.area_polygon),

    re_path(r'^point/$', areas.point_form_submitted),
    re_path(r'^point/(?P<srid>[0-9]+)/(?P<x>%s),(?P<y>%s)(?:/(?P<bb>box))?%s$' % (number, number, map_format_end),
            areas.areas_by_point, name='areas-by-point'),
    re_path(r'^point/latlon/(?P<lat>%s),(?P<lon>%s)(?:/(?P<bb>box))?%s$' % (number, number, map_format_end),
            areas.areas_by_point_latlon, name='areas-by-point-latlon'),
    re_path(r'^point/osgb/(?P<e>%s),(?P<n>%s)(?:/(?P<bb>box))?%s$' % (number, number, map_format_end),
            areas.areas_by_point_osgb, name='areas-by-point-osgb'),

    re_path(r'^nearest/(?P<srid>[0-9]+)/(?P<x>%s),(?P<y>%s)%s$' % (number, number, format_end), postcodes.nearest),

    re_path(r'^areas/(?P<area_ids>[0-9]+(?:,[0-9]+)*)%s$' % map_format_end, areas.areas),
    re_path(r'^areas/(?P<area_ids>[0-9]+(?:,[0-9]+)*)%s$' % data_format_end, areas.areas_polygon),
    re_path(r'^areas/(?P<srid>[0-9]+)/(?P<area_ids>[0-9]+(?:,[0-9]+)*)%s$' % data_format_end, areas.areas_polygon),
    re_path(r'^areas/(?P<area_ids>[0-9]+(?:,[0-9]+)*)/geometry$', areas.areas_geometry),
    re_path(r'^areas/(?P<type>[A-Z0-9,]*[A-Z0-9]+)%s$' % map_format_end, areas.areas_by_type),
    re_path(r'^areas/(?P<type>[A-Z0-9,]*[A-Z0-9]+)%s$' % data_format_end, areas.areas_by_type),
    re_path(r'^areas/(?P<name>.+?)%s$' % map_format_end, areas.areas_by_name),
    re_path(r'^areas$', areas.deal_with_POST, {'call': 'areas'}),
    re_path(r'^code/(?P<code_type>[^/]+)/(?P<code_value>[^/]+?)%s$' % format_end, areas.area_from_code),
]

# Include app-specific urls
if settings.MAPIT_COUNTRY == 'IT':
    urlpatterns.append(
        re_path(r'^', include('mapit_it.urls')),
    )
