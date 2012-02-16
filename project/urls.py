from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

handler500 = 'mapit.shortcuts.json_500'

urlpatterns = patterns('',
    (r'^', include('mapit.urls')),
    (r'^admin/', include(admin.site.urls)),
)
