from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^postcode/(?P<postcode>[a-z0-9]+)(?:\.(?P<format>json))?$(?i)', 'mapit.postcodes.views.postcode'),
    (r'^admin/', include(admin.site.urls)),
)
