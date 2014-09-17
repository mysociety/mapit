from django.conf.urls import patterns, include
from django.contrib import admin
admin.autodiscover()

handler500 = 'mapit.shortcuts.json_500'

urlpatterns = patterns('',
    (r'^', include('mapit.urls')),
    (r'^admin/', include(admin.site.urls)),
)
