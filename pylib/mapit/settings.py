import os
import sys
import django

from django.core.exceptions import ImproperlyConfigured


package_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
paths = (
    os.path.normpath(package_dir + "/../../pylib"),
    os.path.normpath(package_dir + "/../../commonlib/pylib"),
)
for path in paths:
    if path not in sys.path:
        sys.path.append(path)

import mysociety.config
mysociety.config.set_file(os.path.abspath(package_dir + "/../../conf/general"))

# Django settings for mapit project.

if int(mysociety.config.get('STAGING')):
    CACHE_BACKEND = 'dummy://'
    CACHE_MIDDLEWARE_SECONDS = 0
else:
    CACHE_BACKEND = 'memcached://127.0.0.1:11211/?timeout=86400'
    CACHE_MIDDLEWARE_SECONDS = 86400
    CACHE_MIDDLEWARE_KEY_PREFIX = ''
    CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

DEBUG = True if int(mysociety.config.get('STAGING')) else False
TEMPLATE_DEBUG = DEBUG

SERVER_EMAIL = mysociety.config.get('BUGS_EMAIL')
ADMINS = (
    ('mySociety bugs', mysociety.config.get('BUGS_EMAIL')),
)

MANAGERS = ADMINS

if django.get_version() >= '1.2':
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': mysociety.config.get('MAPIT_DB_NAME'),
            'USER': mysociety.config.get('MAPIT_DB_USER'),
            'PASSWORD': mysociety.config.get('MAPIT_DB_PASS'),
            'HOST': mysociety.config.get('MAPIT_DB_HOST'),
            'PORT': mysociety.config.get('MAPIT_DB_PORT'),
        }
    }
else:
    DATABASE_ENGINE = 'postgresql_psycopg2'
    DATABASE_NAME = mysociety.config.get('MAPIT_DB_NAME')
    DATABASE_USER = mysociety.config.get('MAPIT_DB_USER')
    DATABASE_PASSWORD = mysociety.config.get('MAPIT_DB_PASS')
    DATABASE_HOST = mysociety.config.get('MAPIT_DB_HOST')
    DATABASE_PORT = mysociety.config.get('MAPIT_DB_PORT')

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
if mysociety.config.get('COUNTRY') == 'GB':
    TIME_ZONE = 'Europe/London'
    LANGUAGE_CODE = 'en-gb'
elif mysociety.config.get('COUNTRY') == 'NO':
    TIME_ZONE = 'Europe/Oslo'
    LANGUAGE_CODE = 'no'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = mysociety.config.get('DJANGO_SECRET_KEY')

# List of callables that know how to import templates from various sources.
if django.get_version() >= '1.2':
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
#         'django.template.loaders.eggs.load_template_source',
    )
else:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.load_template_source',
        'django.template.loaders.app_directories.load_template_source',
#         'django.template.loaders.eggs.load_template_source',
    )

# UpdateCacheMiddleware does ETag setting, and
# ConditionalGetMiddleware does ETag checking.
# So we don't want this flag, which runs very
# similar ETag code in CommonMiddleware.
USE_ETAGS = False

MIDDLEWARE_CLASSES = (
    'mapit.middleware.gzip.GZipMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'mapit.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'mapit.middleware.cache.FetchFromCacheMiddleware',
    'mapit.middleware.JSONPMiddleware',
)

ROOT_URLCONF = 'mapit.urls'

# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
# Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
TEMPLATE_DIRS = [ package_dir + '/templates' ]

# If the country specific template dir exists add it to the search paths
country_specific_template_path = package_dir + '/templates/' + mysociety.config.get('COUNTRY').lower()
if os.path.exists( country_specific_template_path ):
    TEMPLATE_DIRS.insert( 0, country_specific_template_path )


if django.get_version() >= '1.2':
    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.core.context_processors.request',
        'django.contrib.auth.context_processors.auth',
    )
else:
    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.core.context_processors.request',
        'django.core.context_processors.auth',
        #'django.core.context_processors.debug',
        #'django.core.context_processors.i18n',
        #'django.core.context_processors.media',
    )

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.gis',
    'mapit.areas',
    'mapit.postcodes',
)

# Import the country specific settings
country_specific_module = "country_settings.%s" % mysociety.config.get('COUNTRY')
try:
    module = __import__(country_specific_module, globals(), locals(), ['*'], -1)
    AREA_TYPE_CHOICES    = getattr( module, 'AREA_TYPE_CHOICES' )
    AREA_COUNTRY_CHOICES = getattr( module, 'AREA_COUNTRY_CHOICES' )
    CODE_TYPE_CHOICES    = getattr( module, 'CODE_TYPE_CHOICES' )
except ImportError:
    raise ImproperlyConfigured("Could not load settings from '%s' - perhaps it does not exist?" % country_specific_module)



