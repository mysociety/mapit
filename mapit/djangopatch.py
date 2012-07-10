from django.db.models.sql import RawQuery
from django.db.models.query import RawQuerySet

# This monkeypatches RawQuery/RawQuerySet so that validate_sql (which simply
# checks the query starts with SELECT) isn't called, as it isn't for our query
# and we know what we're doing. This restriction was removed in Django 1.3.

class NoValidateRawQuery(RawQuery):
    def __init__(self, sql, using, params=None):
        # XXX NOT REQUIRED self.validate_sql(sql)
        self.params = params or ()
        self.sql = sql
        self.using = using
        self.cursor = None

        # Mirror some properties of a normal query so that
        # the compiler can be used to process results.
        self.low_mark, self.high_mark = 0, None  # Used for offset/limit
        self.extra_select = {}
        self.aggregate_select = {}

class NoValidateRawQuerySet(RawQuerySet):
    def __init__(self, raw_query, model=None, query=None, params=None,
        translations=None, using=None):
        self.raw_query = raw_query
        self.model = model
        self._db = using
        self.query = query or NoValidateRawQuery(sql=raw_query, using=self.db, params=params)
        self.params = params or ()
        self.translations = translations or {}



