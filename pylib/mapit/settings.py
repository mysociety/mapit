import os
import sys

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

CACHE_BACKEND = 'memcached://127.0.0.1:11211/?timeout=3600'
CACHE_MIDDLEWARE_SECONDS = 3600
CACHE_MIDDLEWARE_KEY_PREFIX = ''
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SERVER_EMAIL = mysociety.config.get('BUGS_EMAIL')
ADMINS = (
    ('mySociety bugs', mysociety.config.get('BUGS_EMAIL')),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = mysociety.config.get('MAPIT_DB_NAME')             # Or path to database file if using sqlite3.
DATABASE_USER = mysociety.config.get('MAPIT_DB_USER')            # Not used with sqlite3.
DATABASE_PASSWORD = mysociety.config.get('MAPIT_DB_PASS')          # Not used with sqlite3.
DATABASE_HOST = mysociety.config.get('MAPIT_DB_HOST')              # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = mysociety.config.get('MAPIT_DB_PORT')              # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

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
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'mapit.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'mapit.cache.FetchFromCacheMiddleware',
)

ROOT_URLCONF = 'mapit.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    package_dir + '/templates',
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
