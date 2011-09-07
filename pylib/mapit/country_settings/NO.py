AREA_TYPE_CHOICES = (
    ('EUP', 'European Parliament'),
    ('EUR', 'European region'),
    ('Norway', (
        ('NFY', 'Norway Fylke'),
        ('NKO', 'Norway Kommune'),
        ('NRA', 'Norway Public Roads Administration'),
        ('NPT', 'Norway Pubic Transport Administration'),
        ('NPG', 'Norway Power Grid Administration'),
        ('NRR', 'Norway Railroad Administration'),
        ('NSA', 'Norway Shoreline Administration'),
    )),
)

AREA_COUNTRY_CHOICES = (
    ('O', 'Norway'),
    ('', '-'),
)

CODE_TYPE_CHOICES = (
    ('n5000', 'Norway code as given in N5000'),
    ('osm', 'OSM'),
)

NAME_TYPE_CHOICES = (
    ('S', 'ONS (SNAC/GSS)'),
    ('M', 'Override name'),
    ('Nno', 'Norwegian - no'),
    ('Nsmi', 'Norwegian - smi'),
    ('Nfi', 'Norwegian - fi'),
)