# Shared functions for postcode and area importing.

import re
import sys
from xml.sax.handler import ContentHandler

from django.core.management.base import LabelCommand
from django.conf import settings
from mapit.models import Postcode

class KML(ContentHandler):
    def __init__(self, *args, **kwargs):
        self.content = ''
        self.data = {}

    def characters(self, content):
        self.content += content

    def normalize_whitespace(s):
        return re.sub('(?us)\s+', ' ', s).strip()

    def endElement(self, name):
        if name == 'name':
            self.current = {}
            self.data[self.normalize_whitespace(self.content)] = self.current
        elif name == 'value':
            self.current[self.name] = self.content.strip()
            self.name = None
        self.content = ''

    def startElement(self, name, attr):
        if name == 'Data':
            self.name = self.normalize_whitespace(attr['name'])

def save_polygons(lookup):
    for shape in lookup.values():
        m, poly = shape
        if not poly:
            continue
        sys.stdout.write(".")
        sys.stdout.flush()
        #g = OGRGeometry(OGRGeomType('MultiPolygon'))
        m.polygons.all().delete()
        for p in poly:
            if p.geom_name == 'POLYGON':
                shapes = [ p ]
            else:
                shapes = p
            for g in shapes:
                # XXX Using g.wkt directly when importing Norway KML works fine
                # with Django 1.1, Postgres 8.3, PostGIS 1.3.3 but fails with
                # Django 1.2, Postgres 8.4, PostGIS 1.5.1, saying that the
                # dimensions constraint fails - because it is trying to import
                # a shape as 3D as the WKT contains " 0" at the end of every
                # co-ordinate. Removing the altitudes from the KML, and/or
                # using altitudeMode makes no difference to the WKT here, so
                # the only easy solution appears to be removing the altitude
                # directly from the WKT before using it.
                #must_be_two_d = g.wkt.replace(' 0,', ',')
                #m.polygons.create(polygon=must_be_two_d)
                m.polygons.create(polygon=g.geos)
        #m.polygon = g.wkt
        #m.save()
        poly[:] = [] # Clear the polygon's list, so that if it has both an ons_code and unit_id, it's not processed twice
    print ""

class PostcodeCommand(LabelCommand):
    help = 'Import postcodes in some way; subclass this!'
    args = '<data files>'
    count = { 'total': 0, 'updated': 0, 'unchanged': 0, 'created': 0 }

    def print_stats(self):
        print "Imported %d (%d new, %d changed, %d same)" % (
            self.count['total'], self.count['created'],
            self.count['updated'], self.count['unchanged']
        )

    # Want to compare co-ordinates so can't use straightforward
    # update_or_create
    def do_postcode(self, postcode, location):
	try:
            pc = Postcode.objects.get(postcode=postcode)
            if location:
                curr_location = ( pc.location[0], pc.location[1] )
                if settings.MAPIT_COUNTRY == 'GB':
                    if pc.postcode[0:2] == 'BT':
                        curr_location = pc.as_irish_grid()
                    else:
                        pc.location.transform(27700) # Postcode locations are stored as WGS84
                        curr_location = ( pc.location[0], pc.location[1] )
                    curr_location = map(round, curr_location)
                if curr_location[0] != location[0] or curr_location[1] != location[1]:
                    pc.location = location
                    pc.save()
                    self.count['updated'] += 1
                else:
                    self.count['unchanged'] += 1
            else:
                self.count['unchanged'] += 1
        except Postcode.DoesNotExist:
            pc = Postcode.objects.create(postcode=postcode, location=location)
            self.count['created'] += 1
        self.count['total'] += 1
        if self.count['total'] % self.often == 0:
            self.print_stats()
        return pc
