import json
import logging
import os
import copy
from io import BytesIO

import attr
from six import text_type
from twisted.internet import address
import twisted.logger
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto

from sydent.sydent import Sydent, parse_config_dict

FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEbG9vZzANBgkqhkiG9w0BAQsFADBvMQswCQYDVQQGEwJV
UzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCk1vdW50YWluIFZpZXcxFjAUBgNVBAoT
DVN5ZG50IHRlc3QgQ0ExGDAWBgNVBAMTD3d3dy5leGFtcGxlLmNvbTAeFw0yMTA1
MDEwMDAwMDBaFw0zMTA0MjkwMDAwMDBaMG8xCzAJBgNVBAYTAlVTMQswCQYDVQQI
EwJDQTETMBEGA1UEBxMKTW91bnRhaW4gVmlldzEWMBQGA1UEChMNU3lkZW50IHRl
c3QgQ0ExGDAWBgNVBAMTD3d3dy5leGFtcGxlLmNvbTCCASIwDQYJKoZIhvcNAQEB
BQADggEPADCCAQoCggEBAL6VYV6K6V6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5e
V6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5e
V6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5e
V6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5e
V6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5e
V6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5e
V6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5eV6c5e
-----END CERTIFICATE-----"""

def make_sydent(test_config=None):
    if test_config is not None and not isinstance(test_config, dict):
        raise TypeError("test_config must be a dict or None")
    config = copy.deepcopy(test_config) if test_config is not None else {}
    if not isinstance(config, dict):
        raise TypeError("config must be a dict")
    config.setdefault('db.file', ':memory:')
    reactor = MemoryReactorClock()
    return Sydent(reactor=reactor, cfg=parse_config_dict(config))

@attr.s(slots=True, auto_attribs=True)
class FakeChannel:
    site: Site
    _reactor = attr.ib()
    result: dict = attr.ib(factory=dict)
    _producer = attr.ib(default=None)

    @property
    def json_body(self):
        if not self.result:
            raise RuntimeError("Result is empty")
        body = self.result.get('body', b'')
        if not body:
            return None
        try:
            return json.loads(body.decode('utf-8', errors='ignore'))
        except Exception:
            return None

    @property
    def code(self):
        if not self.result:
            raise RuntimeError("Result is empty")
        return self.result.get('code')

    @property
    def headers(self):
        if not self.result:
            raise RuntimeError("Result is empty")
        return self.result.get('headers')

    def writeHeaders(self, code, headers):
        if not isinstance(code, int):
            raise TypeError("code must be int")
        if not isinstance(headers, Headers):
            raise TypeError("headers must be Headers")
        self.result['code'] = code
        self.result['headers'] = dict(headers.getAllRawHeaders())

    def write(self, data):
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")
        self.result.setdefault('body', b'')
        self.result['body'] += data

    def registerProducer(self, producer, streaming):
        self._producer = producer

    def unregisterProducer(self):
        self._producer = None

    def requestDone(self):
        self.result['done'] = True

    def getPeer(self):
        return address.IPv4Address('TCP', '127.0.0.1', 0)

    def getHost(self):
        return address.IPv4Address('TCP', '127.0.0.1', 0)

    @property
    def transport(self):
        return self

    def getPeerCertificate(self):
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM)

class FakeSite:
    pass

def make_request(
    reactor,
    method,
    path,
    content=b"",
    access_token=None,
    request=Request,
    shorthand=True,
    federation_auth_origin=None,
):
    if not isinstance(method, (bytes, str)):
        raise TypeError("method must be bytes or str")
    if not isinstance(path, (bytes, str)):
        raise TypeError("path must be bytes or str")
    method_bytes = method.encode('ascii') if isinstance(method, str) else method
    path_bytes = path.encode('ascii') if isinstance(path, str) else path
    if shorthand and not path_bytes.startswith(b"/_matrix"):
        path_bytes = b"/_matrix/identity/v2/" + path_bytes.lstrip(b"/")
    if not path_bytes.startswith(b"/"):
        path_bytes = b"/" + path_bytes
    # normalize duplicate slashes
    while b"//" in path_bytes:
        path_bytes = path_bytes.replace(b"//", b"/")
    if isinstance(content, dict):
        body_bytes = json.dumps(content).encode('utf-8')
    elif isinstance(content, text_type):
        body_bytes = content.encode('utf-8')
    elif isinstance(content, (bytes, bytearray)):
        body_bytes = bytes(content)
    else:
        raise TypeError("content must be dict, str, bytes, or bytearray")
    site = FakeSite()
    channel = FakeChannel(site=site, _reactor=reactor)
    req = request(channel)
    req.process = lambda: b""
    req.content = BytesIO(body_bytes)
    req.postpath = [unquote(p) for p in path_bytes.lstrip(b"/").split(b"/")]
    if access_token is not None:
        if not isinstance(access_token, str):
            raise TypeError("access_token must be str")
        auth_val = b"Bearer " + access_token.encode('utf-8')
        req.requestHeaders.addRawHeader(b"Authorization", auth_val)
    if federation_auth_origin is not None:
        origin_bytes = (federation_auth_origin.encode('utf-8')
                       if isinstance(federation_auth_origin, str)
                       else federation_auth_origin)
        header_val = b"X-Matrix origin=%s,key=,sig=" % origin_bytes
        req.requestHeaders.addRawHeader(b"Authorization", header_val)
    if body_bytes:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method_bytes, path_bytes, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    tx_log = twisted.logger.Logger()

    def emit(self, record):
        try:
            msg = self.format(record)
            level_name = record.levelname.lower()
            if level_name == "warning":
                level_name = "warn"
            try:
                log_level = twisted.logger.LogLevel(level_name)
            except Exception:
                log_level = twisted.logger.LogLevel("info")
            self.tx_log.emit(msg, logLevel=log_level)
        except Exception:
            self.handleError(record)

def setup_logging():
    root = logging.getLogger()
    fmt = "%(asctime)s %(name)s:%(lineno)d %(levelname)s %(message)s"
    formatter = logging.Formatter(fmt)
    if not any(isinstance(h, ToTwistedHandler) for h in root.handlers):
        handler = ToTwistedHandler()
        handler.setFormatter(formatter)
        root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR").upper()
    level = getattr(logging, level_name, logging.ERROR)
    root.setLevel(level)

setup_logging()