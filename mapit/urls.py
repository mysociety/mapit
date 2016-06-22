from django.conf.urls import include, url
from django.conf import settings
from django.shortcuts import render

from mapit.views import areas, postcodes

handler500 = 'mapit.shortcuts.json_500'

format_end = '(?:\.(?P<format>html|json))?'

number = '-?\d*\.?\d+'

urlpatterns = [
    url(r'^$', render, {'template_name': 'mapit/index.html'}, 'mapit_index'),
    url(r'^licensing$', render, {'template_name': 'mapit/licensing.html'}),
    url(r'^overview$', render, {'template_name': 'mapit/overview.html'}),

    url(r'^generations%s$' % format_end, areas.generations, {}, 'mapit_generations'),

    url(r'^postcode/$', postcodes.form_submitted),
    url(r'^postcode/(?P<postcode>[A-Za-z0-9 +]+)%s$' % format_end, postcodes.postcode, name="mapit-postcode"),
    url(r'^postcode/partial/(?P<postcode>[A-Za-z0-9 ]+)%s$' % format_end,
        postcodes.partial_postcode, name="mapit-postcode-partial"),

    url(r'^area/(?P<area_id>[0-9A-Z]+)%s$' % format_end, areas.area, name='area'),
    url(r'^area/(?P<area_id>[0-9]+)/example_postcode%s$' % format_end, postcodes.example_postcode_for_area),
    url(r'^area/(?P<area_id>[0-9]+)/children%s$' % format_end, areas.area_children),
    url(r'^area/(?P<area_id>[0-9]+)/geometry$', areas.area_geometry),
    url(r'^area/(?P<area_id>[0-9]+)/touches%s$' % format_end, areas.area_touches),
    url(r'^area/(?P<area_id>[0-9]+)/overlaps%s$' % format_end, areas.area_overlaps),
    url(r'^area/(?P<area_id>[0-9]+)/covers%s$' % format_end, areas.area_covers),
    url(r'^area/(?P<area_id>[0-9]+)/covered%s$' % format_end, areas.area_covered),
    url(r'^area/(?P<area_id>[0-9]+)/coverlaps%s$' % format_end, areas.area_coverlaps),
    url(r'^area/(?P<area_id>[0-9]+)/intersects%s$' % format_end, areas.area_intersects),
    url(r'^area/(?P<area_id>[0-9A-Z]+)\.(?P<format>kml|geojson|wkt)$', areas.area_polygon, name='area_polygon'),
    url(r'^area/(?P<srid>[0-9]+)/(?P<area_id>[0-9]+)\.(?P<format>kml|json|geojson|wkt)$',
        areas.area_polygon),

    url(r'^point/$', areas.point_form_submitted),
    url(r'^point/(?P<srid>[0-9]+)/(?P<x>%s),(?P<y>%s)(?:/(?P<bb>box))?%s$' % (number, number, format_end),
        areas.areas_by_point, name='areas-by-point'),
    url(r'^point/latlon/(?P<lat>%s),(?P<lon>%s)(?:/(?P<bb>box))?%s$' % (number, number, format_end),
        areas.areas_by_point_latlon, name='areas-by-point-latlon'),
    url(r'^point/osgb/(?P<e>%s),(?P<n>%s)(?:/(?P<bb>box))?%s$' % (number, number, format_end),
        areas.areas_by_point_osgb, name='areas-by-point-osgb'),

    url(r'^nearest/(?P<srid>[0-9]+)/(?P<x>%s),(?P<y>%s)%s$' % (number, number, format_end), postcodes.nearest),

    url(r'^areas/(?P<area_ids>[0-9]+(?:,[0-9]+)*)%s$' % format_end, areas.areas),
    url(r'^areas/(?P<area_ids>[0-9]+(?:,[0-9]+)*)\.(?P<format>kml|geojson)$', areas.areas_polygon),
    url(r'^areas/(?P<srid>[0-9]+)/(?P<area_ids>[0-9]+(?:,[0-9]+)*)\.(?P<format>kml|geojson)$', areas.areas_polygon),
    url(r'^areas/(?P<area_ids>[0-9]+(?:,[0-9]+)*)/geometry$', areas.areas_geometry),
    url(r'^areas/(?P<type>[A-Z0-9,]*[A-Z0-9]+)%s$' % format_end, areas.areas_by_type),
    url(r'^areas/(?P<name>.+?)%s$' % format_end, areas.areas_by_name),
    url(r'^areas$', areas.deal_with_POST, {'call': 'areas'}),
    url(r'^code/(?P<code_type>[^/]+)/(?P<code_value>[^/]+?)%s$' % format_end, areas.area_from_code),
]

# Include app-specific urls
if (settings.MAPIT_COUNTRY == 'GB'):
    urlpatterns.append(
        url(r'^', include('mapit_gb.urls')),
    )
if settings.MAPIT_COUNTRY == 'IT':
    urlpatterns.append(
        url(r'^', include('mapit_it.urls')),
    )
