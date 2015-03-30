import django
from django.template import Library

if django.get_version() >= '1.5':
    from django.template.defaulttags import url as django_url
else:
    from django.templatetags.future import url as django_url

register = Library()


@register.tag
def url(parser, token):
    return django_url(parser, token)
