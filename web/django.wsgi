#!/usr/bin/python 

import os, sys

file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
paths = (
    os.path.normpath(os.path.join(file_dir)),
    os.path.normpath(os.path.join(file_dir, '..'))
)
for path in paths:
    if path not in sys.path:
        sys.path.append(path)

import mapit.settings

if mapit.settings.DEBUG:
    import wsgi_monitor
    wsgi_monitor.start(interval=1.0)

os.environ['DJANGO_SETTINGS_MODULE'] = 'mapit.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

