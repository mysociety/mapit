from ..structural_changes import Command as BaseCommand


class Command(BaseCommand):
    county = 'Buckinghamshire County Council'
    districts = (
        'Aylesbury Vale District Council',
        'South Bucks District Council',
        'Wycombe District Council',
        'Chiltern District Council'
    )
    new_utas = (
        ('Buckinghamshire Council', 'E06000060'),
    )
