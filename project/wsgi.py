#!/usr/bin/env python

import os
import sys
from django.core.wsgi import get_wsgi_application

file_dir = os.path.realpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(file_dir, '..')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

application = get_wsgi_application()
