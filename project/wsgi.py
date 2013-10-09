#!/usr/bin/env python

import os, sys

file_dir = os.path.realpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(file_dir, '..')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
