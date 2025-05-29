from ..structural_changes import Command as BaseCommand


class Command(BaseCommand):
    counties = {
        'Buckinghamshire County Council': (
            'Aylesbury Vale District Council',
            'South Bucks District Council',
            'Wycombe District Council',
            'Chiltern District Council'
        )
    }
    new_utas = (
        ('Buckinghamshire Council', 'E06000060', []),
    )
