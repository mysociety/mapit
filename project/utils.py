from django.http import UnreadablePostError
import importlib


def find_module(c):
    return importlib.machinery.PathFinder.find_spec(c)

# This is taken from the Django documentation:
#   https://docs.djangoproject.com/en/1.9/topics/logging/#django.utils.log.CallbackFilter


def skip_unreadable_post(record):
    if record.exc_info:
        exc_type, exc_value = record.exc_info[:2]
        if isinstance(exc_value, UnreadablePostError):
            return False
    return True
