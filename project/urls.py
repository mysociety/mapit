from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
import settings

handler500 = 'mapit.shortcuts.json_500'

urlpatterns = [
    url(r'^', include('mapit.urls')),
    url(r'^admin/', admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
