from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^(?P<postcode>[a-z0-9]+)(?:\.(?P<format>json))?$(?i)', 'postcodes.views.postcode'),
)
