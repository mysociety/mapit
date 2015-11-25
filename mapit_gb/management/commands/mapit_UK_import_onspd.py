# This script is used to import Northern Ireland postcode information from the
# National Statistics Postcode Database.
# http://www.ons.gov.uk/about-statistics/geography/products/geog-products-postcode/nspd/
#
# The fields of ONSPD Open CSV file are (as of Aug 2015 release)
#  1. Unit postcode - 7 character version
#  2. Unit postcode - 8 character version
#  3. Unit postcode - variable length (e-Gif) version
#  4. Date of introduction
#  5. Date of termination
#  6. County
#  7. Local authority district (LAD)/unitary authority (UA)/ metropolitan
#     district (MD)/ London borough (LB)/ council area (CA)/district council
#     area (DCA)
#  8. (Electoral) ward/division
#  9. Postcode user type
# 10. National grid reference - Easting
# 11. National grid reference - Northing
# 12. Grid reference positional quality indicator
# 13. Former Strategic health authority (SHA)/
#     local health board (LHB)/
#     health board (HB)/
#     health authority (HA)/
#     health & social care board (HSCB)
# 14. Pan SHA
# 15. Country
# 16. Region (formerly GOR)
# 17. Standard (statistical) region (SSR)
# 18. Westminster parliamentary constituency
# 19. European Electoral Region (EER)
# 20. Local Learning and Skills Council (LLSC)/
#     Dept. of Children, Education, Lifelong Learning and Skills (DCELLS)/
#     Enterprise Region (ER)
# 21. Travel-to-work area (TTWA)
# 22. Primary Care Trust (PCT)/
#     Care Trust/
#     Care Trust Plus (CT)/
#     local health board (LHB)/
#     community health partnership (CHP)/
#     local commissioning group (LCG)/
#     primary healthcare directorate (PHD)
# 23. LAU2 areas
# 24. 1991 Census Enumeration District (ED)
# 25. 1991 Census Enumeration District (ED)
# 26. ED positional quality indicator
# 27. Previous Strategic health authority (SHA)/
#     health board (HB)/
#     health authority (HA)/
#     health and social services board (HSSB)
# 28. Local Education Authority (LEA)/
#     Education and Library Board (ELB)
# 29. Health Authority 'old-style'
# 30. 1991 ward (Census code range)
# 31. 1991 ward (OGSS code range)
# 32. 1998 ward
# 33. 2005 'statistical' ward (England and Wales only)
# 34. 2001 Census output area
# 35. Census Area Statistics (CAS) ward
# 36. National park
# 37. 2001 Census lower layer super output area (LSOA)
# 38. 2001 Census middle layer super output area (MSOA)
# 39. 2001 Census urban/rural indicator
# 40. 2001 Census output area classification (OAC)
# 41. 'Old' Primary Care Trust (PCT)/
#     Local Health Board (LHB)/
#     Care Trust (CT)
# 42. 2011 Census output area (OA)/
#     small area
# 43. 2011 Census lower layer super output area (LSOA)/
#     data zone (DZ)/ SOA
# 44. 2011 Census middle layer super output area (MSOA)/
#     intermediate zone (IZ)
# 45. Parish (England)/ community (Wales)
# 46. 2011 Census workplace zone
# 47. Clinical Commissioning Group (CCG)/
#     local health board (LHB)/
#     community health partnership (CHP)/
#     local commissioning group (LCG)/
#     primary healthcare directorate (PHD)
# 48. Built-up area
# 49. Built-up area sub-division
# 50. 2011 Census rural-urban classification
# 51. 2011 Census output area classification (OAC)
# 52. Decimal degrees latitude
# 53. Decimal degrees longitude

from optparse import make_option
from mapit.management.commands.mapit_import_postal_codes import Command


class Command(Command):
    help = 'Imports UK postcodes from the NSPD, excluding NI and Crown Dependencies'
    args = '<ONSPD CSV file>'
    option_defaults = {'header-row': True, 'strip': True, 'srid': 27700, 'coord-field-lon': 10, 'coord-field-lat': 11}
    option_list = Command.option_list + (
        make_option(
            '--allow-terminated-postcodes',
            action='store_true',
            dest='include-terminated',
            default=False,
            help='Set if you want to import terminated postcodes'
        ),
        make_option(
            '--allow-no-location-postcodes',
            action='store_true',
            dest='include-no-location',
            default=False,
            help='Set if you want to import postcodes without location info (quality: 9).  Note that Crown Dependency postcodes have no location and if you choose to import these postcodes they will be imported regardless of your choice for this option.'
        ),
        make_option(
            '--crown-dependencies',
            action='store',
            dest='crown-dependencies',
            default='exclude',
            help=('How to handle crown dependency postocdes.  Set to "include" '
                  'to import them, set to "exclude" to ignore them, set to '
                  '"only" to import only these. (Default: exclude).  Note that '
                  'Crown Dependency postcodes have no location info and are '
                  'imported solely based on this option, regardless of the '
                  'presence of --allow-no-location-postcodes.')
        ),
    )

    def handle_label(self, file, **options):
        # Check our crown-dependencies option is correct
        if not options['crown-dependencies'] in ('include', 'exclude', 'only'):
            raise RuntimeError('Invalid value for --crown-dependencies "%s" must be "include", "exclude", or "only".  ' % options['crown-dependencies'])
        self.process(file, options)

    def pre_row(self, row, options):
        if self.northern_ireland(row):
            return False  # NI handled by other importer
        elif self.reject_row_based_on_termination_data(row, options):
            return False  # Terminated postcode
        elif self.reject_row_based_on_location_data(row, options):
            return False  # go no further unless we want codes with no location
        elif self.reject_row_based_on_crown_dependency_data(row, options):
            return False  # handle crown depenency options
        else:
            return True

    def location_available_for_row(self, row):
        return row[11] != '9'  # PO Box etc.

    def crown_dependency(self, _row):
        return self.code[0:2] in ('GY', 'JE', 'IM')

    def northern_ireland(self, _row):
        return self.code[0:2] == 'BT'

    def reject_row_based_on_location_data(self, row, options):
        if self.location_available_for_row(row):
            return False  # don't reject rows with locations
        elif self.allow_row_with_no_location(row, options):
            return False  # don't reject rows without locations if we allow them
        else:
            return True   # no location and not allowed, reject

    def reject_row_based_on_termination_data(self, row, options):
        return row[4] and not options['include-terminated']

    def allow_row_with_no_location(self, row, options):
        # crown dependencies have no location data in ONSPD so we allow the
        # row and defer the decision to reject the row until we examine the
        # 'crown-dependencies' option.
        return options['include-no-location'] or self.crown_dependency(row)

    def reject_row_based_on_crown_dependency_data(self, row, options):
        if self.crown_dependency_postcode():
            return options['crown-dependencies'] == 'exclude'  # reject if we should exclude these codes
        elif options['crown-dependencies'] == 'only':
            return True  # if we're only importing these codes, reject other codes
        else:
            return False  # otherwise keep
