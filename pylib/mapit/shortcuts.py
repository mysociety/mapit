from django.utils import simplejson
from django.http import HttpResponse
from django.db import connection
from django.conf import settings

class GEOS_JSONEncoder(simplejson.JSONEncoder):
    def default(self, o):
        try:
            return o.json # Will therefore support all the GEOS objects
        except:
            pass
        return super(GEOS_JSONEncoder, self).default(o)

def output_json(out):
    response = HttpResponse(content_type='application/javascript; charset=utf-8')
    if settings.DEBUG:
        simplejson.dump(out, response, ensure_ascii=False, cls=GEOS_JSONEncoder, indent=4)
        simplejson.dump(connection.queries, response, ensure_ascii=False, cls=GEOS_JSONEncoder, indent=4)
    else:
        simplejson.dump(out, response, ensure_ascii=False, cls=GEOS_JSONEncoder)
    return response

