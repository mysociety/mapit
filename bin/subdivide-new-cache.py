#!/usr/bin/env python

from __future__ import print_function

import os
import re
import sys

from boundaries import get_cache_filename

script_directory = os.path.dirname(os.path.abspath(__file__))

cache_directory = os.path.realpath(os.path.join(script_directory,
                                                '..',
                                                'data',
                                                'new-cache'))

for old_filename in os.listdir(cache_directory):
    print("filename is", old_filename)
    m = re.search(r'^(way|node|relation)-(\d+)\.xml$', old_filename)
    if not m:
        print("Ignoring file:", old_filename, file=sys.stderr)
        continue
    element_type, element_id = m.groups()
    full_new_filename = get_cache_filename(element_type, element_id)
    full_old_filename = os.path.join(cache_directory,
                                     old_filename)
    os.rename(full_old_filename, full_new_filename)
