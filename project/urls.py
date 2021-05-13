from django.urls import include, path
from django.contrib import admin

handler500 = 'mapit.shortcuts.json_500'

urlpatterns = [
    path('', include('mapit.urls')),
    path('admin/', admin.site.urls),
]
