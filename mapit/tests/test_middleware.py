from django.test import TestCase
from django.test.client import RequestFactory
from django.http import HttpResponse, HttpResponsePermanentRedirect

from ..middleware import JSONPMiddleware


class JSONPMiddlewareTest(TestCase):

    def setUp(self):
        self.middleware = JSONPMiddleware()
        self.factory = RequestFactory()

    def test_process_response_ignores_302_redirects(self):
        request = self.factory.get("/dummy_url", {"callback": "xyz"})
        response = HttpResponsePermanentRedirect("/new_url")
        middleware_response = self.middleware.process_response(request, response)
        self.assertEqual(middleware_response, response)

    def test_process_response_uses_callback(self):
        request = self.factory.get("/dummy_url", {"callback": "xyz"})
        response = HttpResponse(content="blah")
        middleware_response = self.middleware.process_response(request, response)
        self.assertEqual(middleware_response.content, u'xyz(blah)')

    def test_process_response_uses_ignores_requests_without_callback(self):
        request = self.factory.get("/dummy_url")
        response = HttpResponse(content="blah")
        middleware_response = self.middleware.process_response(request, response)
        self.assertEqual(middleware_response, response)

    def test_process_response_callback_allowed_characters(self):
        request = self.factory.get("/dummy_url", {"callback": "xyz123_$."})
        response = HttpResponse(content="blah")
        middleware_response = self.middleware.process_response(request, response)
        self.assertEqual(middleware_response.content, u'xyz123_$.(blah)')

        # Try with a character not allowed in the callback
        request = self.factory.get("/dummy_url", {"callback": "xyz123_$.["})
        response = HttpResponse(content="blah")
        middleware_response = self.middleware.process_response(request, response)
        self.assertEqual(middleware_response, response)

