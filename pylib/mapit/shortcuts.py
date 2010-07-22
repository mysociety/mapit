from django.utils import simplejson
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, Http404
from django.db import connection
from django.conf import settings
from django.shortcuts import get_object_or_404 as orig_get_object_or_404

class GEOS_JSONEncoder(simplejson.JSONEncoder):
    def default(self, o):
        try:
            return o.json # Will therefore support all the GEOS objects
        except:
            pass
        return super(GEOS_JSONEncoder, self).default(o)

def output_json(out, code=200):
    if code == 400:
        response_type = HttpResponseBadRequest
    elif code == 404:
        response_type = HttpResponseNotFound
    else:
        response_type = HttpResponse
    response = response_type(content_type='application/javascript; charset=utf-8')
    if settings.DEBUG:
        if isinstance(out, dict):
            out['debug_db_queries'] = connection.queries
        simplejson.dump(out, response, ensure_ascii=False, cls=GEOS_JSONEncoder, indent=4)
    else:
        simplejson.dump(out, response, ensure_ascii=False, cls=GEOS_JSONEncoder)
    return response

def get_object_or_404(klass, *args, **kwargs):
    try:
        return orig_get_object_or_404(klass, *args, **kwargs)
    except Http404, e:
        return output_json({ 'error': str(e) }, code=404)


