# https://www.legislation.gov.uk/uksi/2020/156/schedule/made

from ..structural_changes import Command as BaseCommand


class Command(BaseCommand):
    county = 'Northamptonshire County Council'
    districts = (
        'Corby Borough Council',
        'Daventry District Council',
        'East Northamptonshire District Council',
        'Kettering Borough Council',
        'Northampton Borough Council',
        'South Northamptonshire District Council',
        'Wellingborough Borough Council',
    )
    new_utas = (
        ('North Northamptonshire Council', 'E06000061'),
        ('West Northamptonshire Council', 'E06000062'),
    )
