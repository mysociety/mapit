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
        ('North Northamptonshire', 'E06000061',
         ['Corby Borough Council',
          'East Northamptonshire District Council',
          'Kettering Borough Council'
          'Wellingborough Borough Council']),
        ('West Northamptonshire', 'E06000062',
         ['Daventry District Council',
          'Northampton Borough Council',
          'South Northamptonshire District Council']),
    )
