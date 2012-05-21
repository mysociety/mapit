#!/usr/bin/env python

import sys, re
from lxml.html import parse
from lxml import etree

url = "http://wiki.openstreetmap.org/wiki/Tag:boundary%3Dadministrative"

root = parse(url).getroot()

def strip_all_tags(element):
    replace_tag_with_text(element, 'br', "\n")
    return ("".join(element.itertext())).strip()

def replace_tag_with_text(root, tag_name, replacement_text):
    for tag in root.xpath(tag_name):
        if tag.tail:
            tag.tail = replacement_text + tag.tail
        else:
            tag.tail = replacement_text
    etree.strip_elements(root, tag_name, with_tail=False)

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

for table in root.cssselect('table.wikitable'):
    for tr in table:
        if len(tr) <= 2:
            continue
        if tr[0].tag == "th":
            headers = [ h.text.strip() for h in table[1] ]
            continue
        country_name = get_country_name(strip_all_tags(tr[0]))
        if len(tr) != len(headers):
            print >> sys.stderr, "Ignoring row of unexpected length (%d)" % (len(tr),)
            continue
        # There's no admin level 0:
        levels = [None]
        levels += [make_missing_none(strip_all_tags(td))
                   for td in tr[1:]]
        print "####", country_name.encode('utf-8')
        for i, s in enumerate(levels):
            print "---- level", i
            if s:
                print "  " + s.encode('utf-8')
            else:
                print "  [No information]"
