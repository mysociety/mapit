from django.conf import settings


def country(request):
    return {
        'country': settings.MAPIT_COUNTRY,
        'postcodes_available': settings.POSTCODES_AVAILABLE,
        'partial_postcodes_available': settings.PARTIAL_POSTCODES_AVAILABLE,
    }


def analytics(request):
    return {'GOOGLE_ANALYTICS': settings.GOOGLE_ANALYTICS}
