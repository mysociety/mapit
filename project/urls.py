from django.conf.urls import include, url
from django.contrib import admin

handler500 = 'mapit.shortcuts.json_500'

urlpatterns = [
    url(r'^', include('mapit.urls')),
    url(r'^admin/', include(admin.site.urls)),
]
