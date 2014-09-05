#!/usr/bin/env python

from __future__ import print_function

import sys, re
from bs4 import BeautifulSoup

from django.utils.six.moves import urllib

url = "http://wiki.openstreetmap.org/wiki/Tag:boundary%3Dadministrative"

f = urllib.request.urlopen(url)
data = f.read()
f.close()

soup = BeautifulSoup(data, "lxml")

def strip_all_tags(element):
    for br in element.find_all('br'):
        br.replaceWith(u"\n")
    return "".join(element.findAll(text=True)).strip()

# Tidy up the country name column - I'm not sure there's an obviously
# smarter way of doing this for the moment:

def get_country_name(s):
    if re.search('(?s)new levels.*Germany', s):
        return 'Germany'
    result = re.sub(r' +[\(/].*', '', s)
    result = re.sub(r'(?ms)$.*', '', result)
    result = re.sub(r'\s+(see also|has it)', '', result)
    result = re.sub(r'(Poland|Portugal|France|Georgia|Germany).*', '\\1', result)
    result = re.sub(r'^(?u)Flag of Isle of Man\s+', '', result)
    return result

def make_missing_none(s):
    if re.search('(?uis)^\s*N/A\s*$', s):
        return None
    else:
        return s

country_to_admin_levels = {}

for table in soup.find_all('table', 'wikitable'):
    rows = table.findAll('tr', recursive=False)
    for row in rows:
        ths = row.findAll('th', recursive=False)
        if ths:
            headers = [th.string.strip() for th in ths]
            continue
        tds = row.findAll('td', recursive=False)
        if len(tds) <= 2:
            continue
        country_name = get_country_name(strip_all_tags(tds[0]))
        if len(tds) != len(headers):
            print("Warning: Ignoring row of unexpected length", len(tds), file=sys.stderr)
            continue
        levels = [None]
        levels += [make_missing_none(strip_all_tags(td))
                   for td in tds[1:]]
        if country_name in country_to_admin_levels:
            print("Warning: Overwriting previous information for country '%s'" % (country_name,), file=sys.stderr)
        country_to_admin_levels[country_name] = levels

for country_name, levels in sorted(country_to_admin_levels.items()):
    print("####", country_name.encode('utf-8'))
    for i, s in enumerate(levels):
        print("---- level", i)
        if s:
            print("  " + s.encode('utf-8'))
        else:
            print("  [No information]")
