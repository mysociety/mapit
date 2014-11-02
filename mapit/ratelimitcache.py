from datetime import datetime, timedelta
import functools
import hashlib

from django.http import HttpResponseForbidden
from django.core.cache import cache
from django.conf import settings


class ratelimit(object):
    "Instances of this class can be used as decorators"
    # This class is designed to be sub-classed
    minutes = 2  # The time period
    requests = 20  # Number of allowed requests in that time period
    # IP addresses or user agents that aren't rate limited
    excluded = settings.MAPIT_RATE_LIMIT

    prefix = 'rl-'  # Prefix for memcache key

    def __init__(self, **options):
        for key, value in options.items():
            setattr(self, key, value)

    def __call__(self, fn):
        def wrapper(request, *args, **kwargs):
            return self.view_wrapper(request, fn, *args, **kwargs)
        functools.update_wrapper(wrapper, fn)
        return wrapper

    def view_wrapper(self, request, fn, *args, **kwargs):
        if not self.should_ratelimit(request):
            return fn(request, *args, **kwargs)

        if request.META.get('REMOTE_ADDR', '') in self.excluded or \
                ('/' in request.META.get('HTTP_USER_AGENT', '') and
                    request.META.get('HTTP_USER_AGENT', '') in self.excluded):
            return fn(request, *args, **kwargs)

        # If we're using the DummyCache backend then no data will
        # actually be stored in the cache, and as a result cache.incr
        # for a key will fail even immediately after cache.add.
        cache_backend = settings.CACHES['default']['BACKEND']
        if cache_backend == 'django.core.cache.backends.dummy.DummyCache':
            return fn(request, *args, **kwargs)

        counts = self.get_counters(request).values()

        # Increment rate limiting counter
        self.cache_incr(self.current_key(request))

        # Have they failed?
        if sum(int(c) for c in counts) >= self.requests:
            return self.disallowed(request)

        return fn(request, *args, **kwargs)

    def cache_get_many(self, keys):
        return cache.get_many(keys)

    def cache_incr(self, key):
        try:
            cache.incr(key)
        except ValueError:
            cache.add(key, 0, self.expire_after())
            cache.incr(key)

    def should_ratelimit(self, request):
        return len(settings.MAPIT_RATE_LIMIT)

    def get_counters(self, request):
        return self.cache_get_many(self.keys_to_check(request))

    def keys_to_check(self, request):
        extra = self.key_extra(request)
        now = datetime.now()
        return [
            '%s%s-%s' % (
                self.prefix,
                extra,
                (now - timedelta(minutes=minute)).strftime('%Y%m%d%H%M')
            ) for minute in range(self.minutes + 1)
        ]

    def current_key(self, request):
        return '%s%s-%s' % (
            self.prefix,
            self.key_extra(request),
            datetime.now().strftime('%Y%m%d%H%M')
        )

    def key_extra(self, request):
        # By default, their IP address is used
        return request.META.get('REMOTE_ADDR', '')

    def disallowed(self, request):
        "Over-ride this method if you want to log incidents"
        return HttpResponseForbidden('Rate limit exceeded')

    def expire_after(self):
        "Used for setting the memcached cache expiry"
        return (self.minutes + 1) * 60


class ratelimit_post(ratelimit):
    "Rate limit POSTs - can be used to protect a login form"
    key_field = None  # If provided, this POST var will affect the rate limit

    def should_ratelimit(self, request):
        return request.method == 'POST'

    def key_extra(self, request):
        # IP address and key_field (if it is set)
        extra = super(ratelimit_post, self).key_extra(request)
        if self.key_field:
            value = hashlib.sha1(request.POST.get(self.key_field, '')).hexdigest()
            extra += '-' + value
        return extra
