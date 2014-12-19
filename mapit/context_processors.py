from django.core.urlresolvers import reverse
from django.conf import settings


def index_url(request):
    return {'INDEX_URL': reverse('mapit_index')}

def country(request):
    return {
        'country': settings.MAPIT_COUNTRY,
        'postcodes_available': settings.POSTCODES_AVAILABLE,
        'partial_postcodes_available': settings.PARTIAL_POSTCODES_AVAILABLE,
    }


def analytics(request):
    return {'GOOGLE_ANALYTICS': settings.GOOGLE_ANALYTICS}
