AREA_TYPE_CHOICES = (
    ('EUP', 'European Parliament'),
    ('EUR', 'European region'),
    ('HOL', 'House of Lords'),
    ('HOC', 'House of Lords constituency'),
    ('WMP', 'UK Parliament'),
    ('WMC', 'UK Parliament constituency'),
    ('Northern Ireland', (
        ('NIA', 'Northern Ireland Assembly'),
        ('NIE', 'Northern Ireland Assembly constituency'),
        ('LGD', 'Northern Irish Council'),
        ('LGE', 'Northern Irish Council electoral area'),
        ('LGW', 'Northern Irish Council ward'),
    )),
    ('England', (
        ('CTY', 'County council'),
        ('CED', 'County council ward'),
        ('DIS', 'District council'),
        ('DIW', 'District council ward'),
        ('GLA', 'Greater London Authority'),
        ('LAC', 'London Assembly constituency'),
        ('LAE', 'London Assembly area (shared)'),
        ('LAS', 'London Assembly area'),
        ('LBO', 'London borough'),
        ('LBW', 'London borough ward'),
        ('MTD', 'Metropolitan district'),
        ('MTW', 'Metropolitan district ward'),
        ('COI', 'Scilly Isles'),
        ('COP', 'Scilly Isles "ward"'),
    )),
    ('SPA', 'Scottish Parliament'),
    ('SPC', 'Scottish Parliament constituency'),
    ('SPE', 'Scottish Parliament region'),
    ('WAS', 'Welsh Assembly'),
    ('WAC', 'Welsh Assembly constituency'),
    ('WAE', 'Welsh Assembly region'),
    ('UTA', 'Unitary Authority'),
    ('UTE', 'Unitary Authority ward (UTE)'),
    ('UTW', 'Unitary Authority ward (UTW)'),
    ('England and Wales', (
        ('CPC', 'Civil Parish'),
        ('OLF', 'Lower Layer Super Output Area (Full)'),
        ('OLG', 'Lower Layer Super Output Area (Generalised)'),
        ('OMF', 'Middle Layer Super Output Area (Full)'),
        ('OMG', 'Middle Layer Super Output Area (Generalised)'),
    )),
)

AREA_COUNTRY_CHOICES = (
    ('E', 'England'),
    ('W', 'Wales'),
    ('S', 'Scotland'),
    ('N', 'Northern Ireland'),
    ('', '-'),
)

CODE_TYPE_CHOICES = (
    ('ons', 'SNAC'),
    ('gss', 'GSS (SNAC replacement)'),
    ('unit_id', 'Boundary-Line (OS Admin Area ID)'),
    ('osm', 'OSM'),
)

NAME_TYPE_CHOICES = (
    ('O', 'Ordnance Survey'),
    ('S', 'ONS (SNAC/GSS)'),
    ('M', 'Override name'),
)

AREA_CHILD_TO_PARENT_MAPPINGS = {
    # child: parent || (parents,)
    'DIW': 'DIS',
    'CED': 'CTY',
    'LBW': 'LBO',
    'LAC': 'GLA',
    'MTW': 'MTD',
    'UTE': 'UTA',
    'UTW': 'UTA',
    'SPC': 'SPE',
    'WAC': 'WAE',
    'CPC': ('DIS', 'UTA', 'MTD', 'LBO', 'COI'),
}
