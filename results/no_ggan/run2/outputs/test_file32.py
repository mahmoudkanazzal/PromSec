import json
import logging
import os
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
...
-----END CERTIFICATE-----"""

def make_sydent(test_config=None):
    cfg = dict(test_config or {})
    if "db.file" not in cfg:
        cfg["db.file"] = ":memory:"
    reactor = MemoryReactorClock()
    return Sydent(reactor=reactor, cfg=parse_config_dict(cfg))

def _sanitize_header_value(value):
    return value.replace(b'\r', b'').replace(b'\n', b'')

@attr.s
class FakeChannel:
    site = attr.ib()
    _reactor = attr.ib()
    result = attr.ib(factory=dict)
    _producer = attr.ib(default=None)

    def write(self, data):
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("write expects bytes")
        self.result.setdefault("body", b"")
        self.result["body"] += data

    def writeHeaders(self, headers):
        sanitized = {}
        for k, vlist in headers.items():
            sanitized_vals = [_sanitize_header_value(v) for v in vlist]
            sanitized[k] = sanitized_vals
        self.result["headers"] = sanitized

    def registerProducer(self, producer, streaming):
        self._producer = producer

    def unregisterProducer(self):
        self._producer = None

    def getPeer(self):
        return address.IPv4Address("TCP", "127.0.0.1", 3423)

    def getPeerCertificate(self):
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM.encode("utf-8"))

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
    if isinstance(method, text_type):
        method_b = method.encode("ascii")
    else:
        method_b = method
    if isinstance(path, text_type):
        path_b = path.encode("ascii")
    else:
        path_b = path
    if shorthand and not path_b.startswith(b"/_matrix"):
        prefix = b"/_matrix/identity/v2"
        if not path_b.startswith(b"/"):
            path_b = b"/" + path_b
        path_b = prefix + path_b
    if not path_b.startswith(b"/"):
        path_b = b"/" + path_b
    if isinstance(content, dict):
        body = json.dumps(content).encode("utf-8")
    elif isinstance(content, text_type):
        body = content.encode("utf-8")
    else:
        body = content
    site = FakeSite()
    channel = FakeChannel(site=site, _reactor=reactor)
    req = request(channel)
    req.process = lambda: b""
    req.content = BytesIO(body)
    req.postpath = []
    req.requestHeaders = Headers()
    if access_token is not None:
        auth_val = b"Bearer " + access_token.encode("utf-8")
        req.requestHeaders.addRawHeader(b"Authorization", _sanitize_header_value(auth_val))
    if federation_auth_origin is not None:
        auth_val = b"X-Matrix origin=" + federation_auth_origin.encode("utf-8") + b",key=,sig="
        req.requestHeaders.addRawHeader(b"Authorization", _sanitize_header_value(auth_val))
    if body:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method_b, path_b, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    tx_log = twisted.logger.Logger()

    def emit(self, record):
        msg = self.format(record)
        level = record.levelname.lower()
        if level == "warning":
            level = "warn"
        log_method = getattr(self.tx_log, level, self.tx_log.error)
        log_method(msg)

def setup_logging():
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    root = logging.getLogger()
    if not any(isinstance(h, ToTwistedHandler) for h in root.handlers):
        handler = ToTwistedHandler()
        handler.setFormatter(logging.Formatter(fmt))
        root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR").upper()
    level = getattr(logging, level_name, logging.ERROR)
    root.setLevel(level)

setup_logging()