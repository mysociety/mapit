from django.test import TestCase
from django.test.client import RequestFactory
from django import http

from ..middleware import JSONPMiddleware


class JSONPMiddlewareTest(TestCase):

    def setUp(self):
        self.middleware = JSONPMiddleware(self.fake_get_response)
        self.factory = RequestFactory()

    def fake_get_response(self, request):
        return self.fake_response

    def test_process_response_ignores_302_redirects(self):
        request = self.factory.get("/dummy_url", {"callback": "xyz"})
        self.fake_response = http.HttpResponsePermanentRedirect("/new_url")
        middleware_response = self.middleware(request)
        self.assertEqual(middleware_response, self.fake_response)

    def test_process_response_uses_callback(self):
        request = self.factory.get("/dummy_url", {"callback": "xyz"})
        self.fake_response = http.HttpResponse(content="blah", content_type='application/json')
        middleware_response = self.middleware(request)
        self.assertEqual(middleware_response.content, b"typeof xyz === 'function' && xyz(blah)")

    def test_process_response_uses_callback_streaming(self):
        request = self.factory.get("/dummy_url", {"callback": "xyz"})
        self.fake_response = http.StreamingHttpResponse("blah", content_type='application/json')
        middleware_response = self.middleware(request)
        self.assertEqual(b''.join(middleware_response.streaming_content), b"typeof xyz === 'function' && xyz(blah)")

    def test_process_response_uses_ignores_requests_without_callback(self):
        request = self.factory.get("/dummy_url")
        self.fake_response = http.HttpResponse(content="blah", content_type='application/json')
        middleware_response = self.middleware(request)
        self.assertEqual(middleware_response, self.fake_response)

    def test_process_response_callback_allowed_characters(self):
        request = self.factory.get("/dummy_url", {"callback": "xyz123_$."})
        self.fake_response = http.HttpResponse(content="blah", content_type='application/json')
        middleware_response = self.middleware(request)
        self.assertEqual(middleware_response.content, b"typeof xyz123_$. === 'function' && xyz123_$.(blah)")

        # Try with a character not allowed in the callback
        request = self.factory.get("/dummy_url", {"callback": "xyz123_$.["})
        self.fake_response = http.HttpResponse(content="blah", content_type='application/json')
        middleware_response = self.middleware(request)
        self.assertEqual(middleware_response, self.fake_response)
