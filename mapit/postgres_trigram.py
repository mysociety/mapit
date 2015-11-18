"""
Classes that represent PostgreSQL database functions.
"""
from django.db.models.expressions import Func, Value
from django.db.models.fields import FloatField
from django.contrib.postgres.lookups import PostgresSimpleLookup
from django.db.models import CharField, TextField


class TrigramBase(Func):
    def __init__(self, expression, string, **extra):
        if not hasattr(string, 'resolve_expression'):
            string = Value(string)
        super(TrigramBase, self).__init__(expression, string, output_field=FloatField(), **extra)


class TrigramSimilarity(TrigramBase):
    function = 'SIMILARITY'


@CharField.register_lookup
@TextField.register_lookup
class TrigramSimilar(PostgresSimpleLookup):
    lookup_name = 'trigram_similar'
    operator = '%%'
