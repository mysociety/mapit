from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^postcode/', include('mapit.postcodes.urls')),
    (r'^admin/', include(admin.site.urls)),
)
