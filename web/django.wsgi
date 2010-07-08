#!/usr/bin/python 

import os, sys

file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
path = os.path.normpath(file_dir + "/../pylib")
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'mapit.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

