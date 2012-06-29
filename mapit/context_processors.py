def country(request):
    from django.conf import settings
    return { 'country': settings.MAPIT_COUNTRY }
