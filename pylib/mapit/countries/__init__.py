from django.conf import settings

if settings.MAPIT_COUNTRY == 'GB':
    from mapit.countries.gb import *
elif settings.MAPIT_COUNTRY == 'NO':
    from mapit.countries.no import *

