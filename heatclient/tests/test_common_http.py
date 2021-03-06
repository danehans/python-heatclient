# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os
import socket

import requests
import testtools

from heatclient.common import http
from heatclient import exc
from heatclient.tests import fakes
from mox3 import mox


class HttpClientTest(testtools.TestCase):

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        super(HttpClientTest, self).setUp()
        self.m = mox.Mox()
        self.m.StubOutWithMock(requests, 'request')
        self.addCleanup(self.m.UnsetStubs)
        self.addCleanup(self.m.ResetAll)

    def test_http_raw_request(self):
        headers = {'Content-Type': 'application/octet-stream',
                   'User-Agent': 'python-heatclient'}

        # Record a 200
        mock_conn = http.requests.request('GET', 'http://example.com:8004',
                                          allow_redirects=True,
                                          headers=headers)
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                200, 'OK',
                {'content-type': 'application/octet-stream'},
                ''))
        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        resp = client.raw_request('GET', '')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('', ''.join([x for x in resp.content]))
        self.m.VerifyAll()

    def test_token_or_credentials(self):
        # Record a 200
        fake200 = fakes.FakeHTTPResponse(
            200, 'OK',
            {'content-type': 'application/octet-stream'},
            '')

        # no token or credentials
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/octet-stream',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(fake200)

        # credentials
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/octet-stream',
                     'User-Agent': 'python-heatclient',
                     'X-Auth-Key': 'pass',
                     'X-Auth-User': 'user'})
        mock_conn.AndReturn(fake200)

        # token suppresses credentials
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/octet-stream',
                     'User-Agent': 'python-heatclient',
                     'X-Auth-Token': 'abcd1234'})
        mock_conn.AndReturn(fake200)

        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        resp = client.raw_request('GET', '')
        self.assertEqual(200, resp.status_code)

        client.username = 'user'
        client.password = 'pass'
        resp = client.raw_request('GET', '')
        self.assertEqual(200, resp.status_code)

        client.auth_token = 'abcd1234'
        resp = client.raw_request('GET', '')
        self.assertEqual(200, resp.status_code)
        self.m.VerifyAll()

    def test_include_pass(self):
        # Record a 200
        fake200 = fakes.FakeHTTPResponse(
            200, 'OK',
            {'content-type': 'application/octet-stream'},
            '')

        # no token or credentials
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/octet-stream',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(fake200)

        # credentials
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/octet-stream',
                     'User-Agent': 'python-heatclient',
                     'X-Auth-Key': 'pass',
                     'X-Auth-User': 'user'})
        mock_conn.AndReturn(fake200)

        # token suppresses credentials
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/octet-stream',
                     'User-Agent': 'python-heatclient',
                     'X-Auth-Token': 'abcd1234',
                     'X-Auth-Key': 'pass',
                     'X-Auth-User': 'user'})
        mock_conn.AndReturn(fake200)

        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        resp = client.raw_request('GET', '')
        self.assertEqual(200, resp.status_code)

        client.username = 'user'
        client.password = 'pass'
        client.include_pass = True
        resp = client.raw_request('GET', '')
        self.assertEqual(200, resp.status_code)

        client.auth_token = 'abcd1234'
        resp = client.raw_request('GET', '')
        self.assertEqual(200, resp.status_code)
        self.m.VerifyAll()

    def test_not_include_pass(self):
        # Record a 200
        fake500 = fakes.FakeHTTPResponse(
            500, 'ERROR',
            {'content-type': 'application/octet-stream'},
            '(HTTP 401)')

        # no token or credentials
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/octet-stream',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(fake500)

        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        e = self.assertRaises(exc.HTTPUnauthorized,
                              client.raw_request, 'GET', '')
        self.assertIn('include-password', str(e))

    def test_region_name(self):
        # Record a 200
        fake200 = fakes.FakeHTTPResponse(
            200, 'OK',
            {'content-type': 'application/octet-stream'},
            '')

        # Specify region name
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/octet-stream',
                     'X-Region-Name': 'RegionOne',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(fake200)

        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        client.region_name = 'RegionOne'
        resp = client.raw_request('GET', '')
        self.assertEqual(200, resp.status_code)
        self.m.VerifyAll()

    def test_http_json_request(self):
        # Record a 200
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                200, 'OK',
                {'content-type': 'application/json'},
                '{}'))
        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        resp, body = client.json_request('GET', '')
        self.assertEqual(200, resp.status_code)
        self.assertEqual({}, body)
        self.m.VerifyAll()

    def test_http_json_request_w_req_body(self):
        # Record a 200
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            body='test-body',
            allow_redirects=True,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                200, 'OK',
                {'content-type': 'application/json'},
                '{}'))
        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        resp, body = client.json_request('GET', '', body='test-body')
        self.assertEqual(200, resp.status_code)
        self.assertEqual({}, body)
        self.m.VerifyAll()

    def test_http_json_request_non_json_resp_cont_type(self):
        # Record a 200
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004', body='test-body',
            allow_redirects=True,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                200, 'OK',
                {'content-type': 'not/json'},
                '{}'))
        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        resp, body = client.json_request('GET', '', body='test-body')
        self.assertEqual(200, resp.status_code)
        self.assertIsNone(body)
        self.m.VerifyAll()

    def test_http_json_request_invalid_json(self):
        # Record a 200
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                200, 'OK',
                {'content-type': 'application/json'},
                'invalid-json'))
        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        resp, body = client.json_request('GET', '')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('invalid-json', body)
        self.m.VerifyAll()

    def test_http_manual_redirect_delete(self):
        mock_conn = http.requests.request(
            'DELETE', 'http://example.com:8004/foo',
            allow_redirects=False,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                302, 'Found',
                {'location': 'http://example.com:8004/foo/bar'},
                ''))
        mock_conn = http.requests.request(
            'DELETE', 'http://example.com:8004/foo/bar',
            allow_redirects=False,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                200, 'OK',
                {'content-type': 'application/json'},
                '{}'))

        self.m.ReplayAll()

        client = http.HTTPClient('http://example.com:8004/foo')
        resp, body = client.json_request('DELETE', '')

        self.assertEqual(200, resp.status_code)
        self.m.VerifyAll()

    def test_http_manual_redirect_prohibited(self):
        mock_conn = http.requests.request(
            'DELETE', 'http://example.com:8004/foo',
            allow_redirects=False,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                302, 'Found',
                {'location': 'http://example.com:8004/'},
                ''))
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004/foo')
        self.assertRaises(exc.InvalidEndpoint,
                          client.json_request, 'DELETE', '')
        self.m.VerifyAll()

    def test_http_json_request_redirect(self):
        # Record the 302
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                302, 'Found',
                {'location': 'http://example.com:8004'},
                ''))
        # Record the following 200
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                200, 'OK',
                {'content-type': 'application/json'},
                '{}'))
        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        resp, body = client.json_request('GET', '')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(body, {})
        self.m.VerifyAll()

    def test_http_404_json_request(self):
        # Record a 404
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                404, 'OK', {'content-type': 'application/json'},
                '{}'))
        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        try:
            client.json_request('GET', '')
            self.fail('No exception raised')
        except exc.HTTPNotFound as e:
            # Assert that the raised exception can be converted to string
            self.assertIsNotNone(e.message)
        self.m.VerifyAll()

    def test_http_300_json_request(self):
        # Record a 300
        mock_conn = http.requests.request(
            'GET', 'http://example.com:8004',
            allow_redirects=True,
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'python-heatclient'})
        mock_conn.AndReturn(
            fakes.FakeHTTPResponse(
                300, 'OK', {'content-type': 'application/json'},
                '{}'))
        # Replay, create client, assert
        self.m.ReplayAll()
        client = http.HTTPClient('http://example.com:8004')
        try:
            client.json_request('GET', '')
            self.fail('No exception raised')
        except exc.HTTPMultipleChoices as e:
            # Assert that the raised exception can be converted to string
            self.assertIsNotNone(e.message)
        self.m.VerifyAll()

    def test_fake_json_request(self):
        headers = {'User-Agent': 'python-heatclient'}
        mock_conn = http.requests.request('GET', 'fake://example.com:8004/',
                                          allow_redirects=True,
                                          headers=headers)
        mock_conn.AndRaise(socket.gaierror)
        self.m.ReplayAll()

        client = http.HTTPClient('fake://example.com:8004')
        self.assertRaises(exc.InvalidEndpoint,
                          client._http_request, "/", "GET")
        self.m.VerifyAll()

    def test_debug_curl_command(self):
        self.m.StubOutWithMock(logging.Logger, 'debug')

        ssl_connection_params = {'ca_file': 'TEST_CA',
                                 'cert_file': 'TEST_CERT',
                                 'key_file': 'TEST_KEY',
                                 'insecure': 'TEST_NSA'}

        headers = {'key': 'value'}

        mock_logging_debug = logging.Logger.debug(
            "curl -i -X GET -H 'key: value' --key TEST_KEY "
            "--cert TEST_CERT --cacert TEST_CA "
            "-k http://foo/bar"
        )
        mock_logging_debug.AndReturn(None)
        self.m.ReplayAll()

        client = http.HTTPClient('http://foo')
        client.ssl_connection_params = ssl_connection_params
        client.log_curl_request('GET', '/bar', {'headers': headers})

        self.m.VerifyAll()

    def test_http_request_socket_error(self):
        headers = {'User-Agent': 'python-heatclient'}
        mock_conn = http.requests.request('GET', 'http://example.com:8004/',
                                          allow_redirects=True,
                                          headers=headers)
        mock_conn.AndRaise(socket.error)
        self.m.ReplayAll()

        client = http.HTTPClient('http://example.com:8004')
        self.assertRaises(exc.CommunicationError,
                          client._http_request, "/", "GET")
        self.m.VerifyAll()

    def test_http_request_socket_timeout(self):
        headers = {'User-Agent': 'python-heatclient'}
        mock_conn = http.requests.request('GET', 'http://example.com:8004/',
                                          allow_redirects=True,
                                          headers=headers)
        mock_conn.AndRaise(socket.timeout)
        self.m.ReplayAll()

        client = http.HTTPClient('http://example.com:8004')
        self.assertRaises(exc.CommunicationError,
                          client._http_request, "/", "GET")
        self.m.VerifyAll()

    def test_get_system_ca_file(self):
        chosen = '/etc/ssl/certs/ca-certificates.crt'
        self.m.StubOutWithMock(os.path, 'exists')
        os.path.exists(chosen).AndReturn(chosen)
        self.m.ReplayAll()

        ca = http.get_system_ca_file()
        self.assertEqual(ca, chosen)

        self.m.VerifyAll()

    def test_insecure_verify_cert_None(self):
        client = http.HTTPClient('https://foo', insecure=True)
        self.assertFalse(client.verify_cert)

    def test_passed_cert_to_verify_cert(self):
        client = http.HTTPClient('https://foo', ca_file="NOWHERE")
        self.assertEqual(client.verify_cert, "NOWHERE")

        self.m.StubOutWithMock(http, 'get_system_ca_file')
        http.get_system_ca_file().AndReturn("SOMEWHERE")
        self.m.ReplayAll()
        client = http.HTTPClient('https://foo')
        self.assertEqual(client.verify_cert, "SOMEWHERE")
