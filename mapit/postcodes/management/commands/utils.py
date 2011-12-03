# Shared functions for postcode importing.

from django.core.management.base import LabelCommand
from django.conf import settings
from mapit.postcodes.models import Postcode

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
