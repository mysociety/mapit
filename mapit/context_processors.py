from django.conf import settings


def country(request):
    return {'country': settings.MAPIT_COUNTRY}


def analytics(request):
    return {'GOOGLE_ANALYTICS': settings.GOOGLE_ANALYTICS}
