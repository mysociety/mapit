import os
import sys
import yaml
import django

# Make sure the application in this repository is on the path
package_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
path = os.path.abspath( os.path.join( package_dir, '..' ) )

# We don't want two copies of this on the path, so remove it if it's
# already there.
while path in sys.path:
    sys.path.remove(path)

sys.path.insert(0, path)

# The mySociety deployment system works by having a conf directory at the root
# of the repo, containing a general.yml file of options. Use that file if
# present. Obviously you can just edit any part of this file, it is a normal
# Django settings.py file.
try:
    config = yaml.load( open(os.path.normpath(package_dir + "/../conf/general.yml"), 'r') )
except:
    config = {}

# An EPSG code for what the areas are stored as, e.g. 27700 is OSGB, 4326 for
# WGS84. Optional, defaults to 4326.
MAPIT_AREA_SRID = int(config.get('AREA_SRID', 4326))

# Country is currently one of GB, NO, or KE. Optional; country specific things
# won't happen if not set.
MAPIT_COUNTRY = config.get('COUNTRY', '')

# A list of IP addresses or User Agents that should be excluded from rate
# limiting. Optional.
MAPIT_RATE_LIMIT = config.get('RATE_LIMIT', [])

# Django settings for mapit project.

DEBUG = config.get('DEBUG', True)
TEMPLATE_DEBUG = DEBUG

if DEBUG:
    CACHE_BACKEND = 'dummy://'
    CACHE_MIDDLEWARE_SECONDS = 0
else:
    CACHE_BACKEND = 'memcached://127.0.0.1:11211/?timeout=86400'
    CACHE_MIDDLEWARE_SECONDS = 86400
    CACHE_MIDDLEWARE_KEY_PREFIX = config.get('MAPIT_DB_NAME')
    CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

if config.get('BUGS_EMAIL'):
    SERVER_EMAIL = config['BUGS_EMAIL']
    ADMINS = (
        ('mySociety bugs', config['BUGS_EMAIL']),
    )
    MANAGERS = ADMINS

if django.get_version() >= '1.2':
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': config.get('MAPIT_DB_NAME', 'mapit'),
            'USER': config.get('MAPIT_DB_USER', 'mapit'),
            'PASSWORD': config.get('MAPIT_DB_PASS', ''),
            'HOST': config.get('MAPIT_DB_HOST', ''),
            'PORT': config.get('MAPIT_DB_PORT', ''),
        }
    }
else:
    DATABASE_ENGINE = 'postgresql_psycopg2'
    DATABASE_NAME = config.get('MAPIT_DB_NAME', 'mapit')
    DATABASE_USER = config.get('MAPIT_DB_USER', 'mapit')
    DATABASE_PASSWORD = config.get('MAPIT_DB_PASS', '')
    DATABASE_HOST = config.get('MAPIT_DB_HOST', '')
    DATABASE_PORT = config.get('MAPIT_DB_PORT', '')

# Make this unique, and don't share it with anybody.
SECRET_KEY = config.get('DJANGO_SECRET_KEY', '')

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
if MAPIT_COUNTRY == 'GB':
    TIME_ZONE = 'Europe/London'
    LANGUAGE_CODE = 'en-gb'
elif MAPIT_COUNTRY == 'NO':
    TIME_ZONE = 'Europe/Oslo'
    LANGUAGE_CODE = 'no'
else:
    TIME_ZONE = 'Europe/London'
    LANGUAGE_CODE = 'en'

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

# List of callables that know how to import templates from various sources.
if django.get_version() >= '1.2':
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        # Needs adapting to new class version
        'mapit.loader.load_template_source',
    )
else:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.load_template_source',
        'mapit.loader.load_template_source',
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
    'mapit.middleware.ViewExceptionMiddleware',
)

ROOT_URLCONF = 'urls'

# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
# Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
TEMPLATE_DIRS = (
    os.path.join( package_dir, 'templates', MAPIT_COUNTRY.lower() ),
    os.path.join( package_dir, 'templates' ),
)

if django.get_version() >= '1.2':
    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.core.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'mapit.context_processors.country',
    )
else:
    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.core.context_processors.request',
        'django.core.context_processors.auth',
        'mapit.context_processors.country',
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

    'south',
    'mapit',
)

# use staticfiles if Django recent enough. If not then trust that the webserver
# can handle serving the content. mySociety currently runs mapit on Django 1.2.x
# as that is the version in the Debian Squeeze package.
if django.get_version() >= '1.3':
    INSTALLED_APPS += ( 'django.contrib.staticfiles', )
    STATIC_URL = '/static'
