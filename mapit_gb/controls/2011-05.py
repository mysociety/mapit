# A control file for importing Boundary-Line.
# CEDs don't have ONS codes, so we have to have something manual
# to e.g. tell us if some county council wards have changed.
#
# This edition of Boundary-Line uses the new SNAC codes

from areas.models import Area, Generation


def code_version():
    return 'gss'


# Renames
# Eastleigh: Parish of Allbrook renamed Allbrook and North Boyatt
# North Norfolk: Parish of Aldborough renamed  Aldborough & Thurgarton
# Sevenoaks: Ash Ward renamed  Ash and New Ash Green
# Harrogate: Parish of Markingfield renamed Markenfield
# Wiltshire: Parishes of Allcannings and Bower Chalke renamed All Cannings and Bowerchalke

def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match against ONS code,
       or an Area to be used as an override instead"""

    # There appears to be a regression, in that new areas introduced, I
    # believe, correctly by October 2010 Boundary-Line (due to WSI 2010/1481:
    # http://www.legislation.gov.uk/wsi/2010/1451/contents/made )
    # have disappeared from May 2011 and it has the previous areas.
    if type == 'UTE' and name in ('Sully ED', 'Dinas Powys ED', 'Plymouth ED', 'Llandough ED'):
        area_within = Area.objects.filter(
            type__code='UTA', polygons__polygon__contains=geometry.geos.point_on_surface)[0]
        if area_within.name == 'Vale of Glamorgan Council':
            current = Generation.objects.current()
            return Area.objects.get(
                names__name=name, names__type='O', parent_area=area_within,
                generation_low__lte=current, generation_high__gte=current)

    # The Scottish Parliament has had boundary changes. New Boundary-Line has
    # ONS codes for this too, hooray!

    # The following have had boundary changes for the 2011 elections, but all
    # have ONS codes and so can be ignored/ detected that way:
    #
    # Redrawn boundaries
    # 2011/3   Cheshire East
    # 2011/4   Cheshire West and Chester
    # 2011/161 Bedford
    # 2011/162 Central Bedfordshire
    # 2011/163 Mansfield
    # 2011/164 Northampton
    # 2011/165 South Derbyshire
    # 2011/166 Sedgemoor
    # 2011/167 Stoke-on-Trent
    # 2011/168 West Somerset
    #
    # Minor changes
    # 2008/176  Maidston
    # 2008/178  Uttlesford
    # 2008/748  2009/533 Stratford-on-Avon
    # 2009/532  Tewkesbury
    # 2009/538  North Norfolk
    # 2009/540  Pendle
    # 2009/542  Mid Devon
    # 2009/543  East Devon
    # 2009/2786 Kettering
    # 2010/684  Huntingdonshire
    # 2010/687  Wellingborough
    # 2010/2108 Tonbridge and Malling
    # 2010/2109 Kirklees
    # 2010/2788 Teignbridge
    # 2010/2943 North Somerset
    # 2011/404  New Forest
    # 2011/406  Rotherham

    # S2010/353 East Dunbarton/ Glasgow

    return False
