import os
import sys
import yaml
import django

package_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
path = os.path.normpath(package_dir + "/../../pylib")
if path not in sys.path:
    sys.path.append(path)

# load the mySociety config
config = yaml.load( open(os.path.normpath(package_dir + "/../../conf/general.yml"), 'r') )

MAPIT_AREA_SRID = int(config.get('AREA_SRID', 4326))
MAPIT_COUNTRY = config.get('COUNTRY', '')
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
    CACHE_MIDDLEWARE_KEY_PREFIX = ''
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
            'NAME': config['MAPIT_DB_NAME'],
            'USER': config['MAPIT_DB_USER'],
            'PASSWORD': config['MAPIT_DB_PASS'],
            'HOST': config['MAPIT_DB_HOST'],
            'PORT': config['MAPIT_DB_PORT'],
        }
    }
else:
    DATABASE_ENGINE = 'postgresql_psycopg2'
    DATABASE_NAME = config['MAPIT_DB_NAME']
    DATABASE_USER = config['MAPIT_DB_USER']
    DATABASE_PASSWORD = config['MAPIT_DB_PASS']
    DATABASE_HOST = config['MAPIT_DB_HOST']
    DATABASE_PORT = config['MAPIT_DB_PORT']

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
SECRET_KEY = config['DJANGO_SECRET_KEY']

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
if MAPIT_COUNTRY == 'GB':
    TEMPLATE_DIRS = (
        package_dir + '/templates',
    )
elif MAPIT_COUNTRY == 'NO':
    TEMPLATE_DIRS = (
        package_dir + '/templates/no',
        package_dir + '/templates',
    )

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
