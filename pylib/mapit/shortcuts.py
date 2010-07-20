from django.utils import simplejson
from django.http import HttpResponse

class GEOS_JSONEncoder(simplejson.JSONEncoder):
    def default(self, o):
        try:
            return o.json # Will therefore support all the GEOS objects
        except:
            pass
        return super(GEOS_JSONEncoder, self).default(o)

def output_json(out):
    response = HttpResponse(content_type='application/javascript; charset=utf-8')
    simplejson.dump(out, response, ensure_ascii=False, cls=GEOS_JSONEncoder)
    return response

