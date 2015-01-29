"""
A copy of Django's gzip middleware, adjusted for 1.4 and
https://code.djangoproject.com/ticket/24242 by including changed
compress_sequence/StreamingBuffer.
"""
from __future__ import absolute_import

import re

from django.utils.text import compress_string, StreamingBuffer as DjangoStreamingBuffer
from django.utils.cache import patch_vary_headers
from gzip import GzipFile

re_accepts_gzip = re.compile(r'\bgzip\b')


class StreamingBuffer(DjangoStreamingBuffer):
    def read(self):
        if not self.vals:
            return b''
        ret = b''.join(self.vals)
        self.vals = []
        return ret


# Like compress_string, but for iterators of strings.
def compress_sequence(sequence):
    buf = StreamingBuffer()
    zfile = GzipFile(mode='wb', compresslevel=6, fileobj=buf)
    # Output headers...
    yield buf.read()
    for item in sequence:
        zfile.write(item)
        data = buf.read()
        if data:
            yield data
    zfile.close()
    yield buf.read()


class GZipMiddleware(object):
    """
    This middleware compresses content if the browser allows gzip compression.
    It sets the Vary header accordingly, so that caches will base their storage
    on the Accept-Encoding header.
    """
    def process_response(self, request, response):
        # It's not worth attempting to compress really short responses.
        if not getattr(response, 'streaming', None) and len(response.content) < 200:
            return response

        # Avoid gzipping if we've already got a content-encoding.
        if response.has_header('Content-Encoding'):
            return response

        patch_vary_headers(response, ('Accept-Encoding',))

        ae = request.META.get('HTTP_ACCEPT_ENCODING', '')
        if not re_accepts_gzip.search(ae):
            return response

        if getattr(response, 'streaming', None):
            # Delete the `Content-Length` header for streaming content, because
            # we won't know the compressed size until we stream it.
            response.streaming_content = compress_sequence(response.streaming_content)
            del response['Content-Length']
        else:
            # Return the compressed content only if it's actually shorter.
            compressed_content = compress_string(response.content)
            if len(compressed_content) >= len(response.content):
                return response
            response.content = compressed_content
            response['Content-Length'] = str(len(response.content))

        if response.has_header('ETag'):
            response['ETag'] = re.sub('"$', ';gzip"', response['ETag'])
        response['Content-Encoding'] = 'gzip'

        return response
