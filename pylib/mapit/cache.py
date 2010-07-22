# Django's cache middleware, patched to use get_full_path() as they can be cached.

from django.conf import settings
from django.core.cache import cache
from django.utils.cache import patch_response_headers, get_max_age, cc_delim_re
from django.utils.encoding import iri_to_uri
from django.utils.hashcompat import md5_constructor

class UpdateCacheMiddleware(object):
    """
    Response-phase cache middleware that updates the cache if the response is
    cacheable.

    Must be used as part of the two-part update/fetch cache middleware.
    UpdateCacheMiddleware must be the first piece of middleware in
    MIDDLEWARE_CLASSES so that it'll get called last during the response phase.
    """
    def __init__(self):
        self.cache_timeout = settings.CACHE_MIDDLEWARE_SECONDS
        self.key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
        self.cache_anonymous_only = getattr(settings, 'CACHE_MIDDLEWARE_ANONYMOUS_ONLY', False)

    def process_response(self, request, response):
        """Sets the cache, if needed."""
        if not hasattr(request, '_cache_update_cache') or not request._cache_update_cache:
            # We don't need to update the cache, just return.
            return response
        if request.method != 'GET':
            # This is a stronger requirement than above. It is needed
            # because of interactions between this middleware and the
            # HTTPMiddleware, which throws the body of a HEAD-request
            # away before this middleware gets a chance to cache it.
            return response
        if not response.status_code == 200:
            return response
        # Try to get the timeout from the "max-age" section of the "Cache-
        # Control" header before reverting to using the default cache_timeout
        # length.
        timeout = get_max_age(response)
        if timeout == None:
            timeout = self.cache_timeout
        elif timeout == 0:
            # max-age was set to 0, don't bother caching.
            return response
        patch_response_headers(response, timeout)
        if timeout:
            cache_key = learn_cache_key(request, response, timeout, self.key_prefix)
            cache.set(cache_key, response, timeout)
        return response

class FetchFromCacheMiddleware(object):
    """
    Request-phase cache middleware that fetches a page from the cache.

    Must be used as part of the two-part update/fetch cache middleware.
    FetchFromCacheMiddleware must be the last piece of middleware in
    MIDDLEWARE_CLASSES so that it'll get called last during the request phase.
    """
    def __init__(self):
        self.cache_timeout = settings.CACHE_MIDDLEWARE_SECONDS
        self.key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
        self.cache_anonymous_only = getattr(settings, 'CACHE_MIDDLEWARE_ANONYMOUS_ONLY', False)

    def process_request(self, request):
        """
        Checks whether the page is already cached and returns the cached
        version if available.
        """
        if self.cache_anonymous_only:
            assert hasattr(request, 'user'), "The Django cache middleware with CACHE_MIDDLEWARE_ANONYMOUS_ONLY=True requires authentication middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.auth.middleware.AuthenticationMiddleware' before the CacheMiddleware."

        if not request.method in ('GET', 'HEAD'):
            request._cache_update_cache = False
            return None # Don't bother checking the cache.

        if self.cache_anonymous_only and request.user.is_authenticated():
            request._cache_update_cache = False
            return None # Don't cache requests from authenticated users.

        cache_key = get_cache_key(request, self.key_prefix)
        if cache_key is None:
            request._cache_update_cache = True
            return None # No cache information available, need to rebuild.

        response = cache.get(cache_key, None)
        if response is None:
            request._cache_update_cache = True
            return None # No cache information available, need to rebuild.

        request._cache_update_cache = False
        return response

# and bits of django/utils/cache.py

def _generate_cache_key(request, headerlist, key_prefix):
    """Returns a cache key from the headers given in the header list."""
    ctx = md5_constructor()
    for header in headerlist:
        value = request.META.get(header, None)
        if value is not None:
            ctx.update(value)
    path = md5_constructor(iri_to_uri(request.get_full_path()))
    return 'views.decorators.cache.cache_page.%s.%s.%s' % (
               key_prefix, path.hexdigest(), ctx.hexdigest())

def _generate_cache_header_key(key_prefix, request):
    """Returns a cache key for the header cache."""
    path = md5_constructor(iri_to_uri(request.get_full_path()))
    return 'views.decorators.cache.cache_header.%s.%s' % (key_prefix, path.hexdigest())

def get_cache_key(request, key_prefix=None):
    """
    Returns a cache key based on the request path. It can be used in the
    request phase because it pulls the list of headers to take into account
    from the global path registry and uses those to build a cache key to check
    against.

    If there is no headerlist stored, the page needs to be rebuilt, so this
    function returns None.
    """
    if key_prefix is None:
        key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
    cache_key = _generate_cache_header_key(key_prefix, request)
    headerlist = cache.get(cache_key, None)
    if headerlist is not None:
        return _generate_cache_key(request, headerlist, key_prefix)
    else:
        return None

def learn_cache_key(request, response, cache_timeout=None, key_prefix=None):
    """
    Learns what headers to take into account for some request path from the
    response object. It stores those headers in a global path registry so that
    later access to that path will know what headers to take into account
    without building the response object itself. The headers are named in the
    Vary header of the response, but we want to prevent response generation.

    The list of headers to use for cache key generation is stored in the same
    cache as the pages themselves. If the cache ages some data out of the
    cache, this just means that we have to build the response once to get at
    the Vary header and so at the list of headers to use for the cache key.
    """
    if key_prefix is None:
        key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
    if cache_timeout is None:
        cache_timeout = settings.CACHE_MIDDLEWARE_SECONDS
    cache_key = _generate_cache_header_key(key_prefix, request)
    if response.has_header('Vary'):
        headerlist = ['HTTP_'+header.upper().replace('-', '_')
                      for header in cc_delim_re.split(response['Vary'])]
        cache.set(cache_key, headerlist, cache_timeout)
        return _generate_cache_key(request, headerlist, key_prefix)
    else:
        # if there is no Vary header, we still need a cache key
        # for the request.path
        cache.set(cache_key, [], cache_timeout)
        return _generate_cache_key(request, [], key_prefix)

