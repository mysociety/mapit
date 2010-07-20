from django.utils import simplejson
from django.http import HttpResponse

def output_json(out):
    response = HttpResponse(content_type='application/javascript; charset=utf-8')
    simplejson.dump(out, response, ensure_ascii=False)
    return response

