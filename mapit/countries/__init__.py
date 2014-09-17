from django.conf import settings

if settings.MAPIT_COUNTRY == 'GB':
    from mapit_gb.countries import *
elif settings.MAPIT_COUNTRY == 'NO':
    from mapit_no.countries import *
elif settings.MAPIT_COUNTRY == 'Global':
    from mapit_global.countries import *

