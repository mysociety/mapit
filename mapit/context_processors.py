from django.conf import settings


def country(request):
    return {
        'country': settings.MAPIT_COUNTRY,
        'area_srid_units': 'degrees' if settings.MAPIT_AREA_SRID == 4326 else 'metres',
        'within_maximum': settings.MAPIT_WITHIN_MAXIMUM,
        'postcodes_available': settings.POSTCODES_AVAILABLE,
        'partial_postcodes_available': settings.PARTIAL_POSTCODES_AVAILABLE,
    }


def analytics(request):
    return {'GOOGLE_ANALYTICS': settings.GOOGLE_ANALYTICS}
