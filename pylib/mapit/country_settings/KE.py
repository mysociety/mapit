AREA_TYPE_CHOICES = (
    ('CTR','Country'),

    ('Kenya', (
        ('PRO', 'Province'),
        ('DIS', 'District'),
        ('DIV', 'Division'),
        ('LOC', 'Location'),
        ('SLC', 'Sublocation'),
    )),
)

AREA_COUNTRY_CHOICES = (
    ('K', 'Kenya'),
)

CODE_TYPE_CHOICES = (
    ('gadm', 'Global Administrative Areas'),
)

NAME_TYPE_CHOICES = (
    ('GADM', 'Global Administrative Areas'),
    ('M', 'Override name'),
)

AREA_CHILD_TO_PARENT_MAPPINGS = {
    # child: parent || (parents,)
    'SLC': 'LOC',
    'LOC': 'DIV',
    'DIV': 'DIS',
    'DIS': 'PRO',
    'PRO': 'CTR',
}
