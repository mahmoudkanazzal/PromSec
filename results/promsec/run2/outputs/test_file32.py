import json
import os
from io import BytesIO
import logging

import attr
from six import text_type
from twisted.internet import address
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto
from sydent.sydent import Sydent
from sydent.sydent import parse_config_dict
from twisted.logger import Logger

FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEbG9vZzANBgkqhkiG9w0BAQsFADBvMQswCQYDVQQGEwJV
UzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCk1vdW50YWluIFZpZXcxFjAUBgNVBAoT
DVN5c3RlbSBJbmMuMRUwEwYDVQQDEwxleGFtcGxlLmNvbTEhMB8GCSqGSIb3DQEJ
ARYSc3VwcG9ydEBleGFtcGxlLmNvbTAeFw0yMTA1MDEwMDAwMDBaFw0zMTA0Mjkw
MDAwMDBaMG8xCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJDQTETMBEGA1UEBxMKTW91
bnRhaW4gVmlldzEWMBQGA1UEChMNU3lzdGVtIEluYy4xFTATBgNVBAMTDGV4YW1w
bGUuY29tMSEwHwYJKoZIhvcNAQkBFhJzdXBwb3J0QGV4YW1wbGUuY29tMIIBIjAN
BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArV6V6w5K5vZc6K6V6V6w5K5vZc6K
6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6w5K
5vZc6K6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V
6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6w5K5v
Zc6K6V6V6w5K5vZc6K6V6V6w5K5vZc6VwIDAQABo1AwTjAdBgNVHQ4EFgQUkK3M
6V6V6w5K5vZc6K6V6V6w5K5vMwHwYDVR0jBBgwFoAUkK3M6V6V6w5K5vZc6K6V6V6
w5K5vMwDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEABcV6V6w5K5vZc
6K6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6w5K5vZc6K6V6V6
-----END CERTIFICATE-----"""

def make_sydent(test_config=None):
    if test_config is None:
        test_config = {}
    config = {"db": {"file": ":memory:"}}
    config.update(test_config)
    if "db" not in test_config or "file" not in test_config.get("db", {}):
        config["db"]["file"] = ":memory:"
    reactor = MemoryReactorClock()
    parsed = parse_config_dict(config)
    return Sydent(reactor, parsed)

@attr.s(slots=True)
class FakeChannel:
    site = attr.ib()
    _reactor = attr.ib()
    result = attr.ib(factory=dict)
    _producer = attr.ib(default=None)

    @property
    def json_body(self):
        if not self.result:
            raise RuntimeError("No result available")
        body = self.result.get("body", b"")
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        return json.loads(body)

    @property
    def code(self):
        if not self.result:
            raise RuntimeError("No result available")
        return int(self.result.get("code", 0))

    @property
    def headers(self):
        if not self.result:
            raise RuntimeError("No result available")
        hdrs = self.result.get("headers", [])
        return Headers(hdrs)

    def writeHeaders(self, code, headers):
        self.result["code"] = code
        self.result["headers"] = list(headers)

    def write(self, data):
        self.result.setdefault("body", b"")
        self.result["body"] += data

    def registerProducer(self, producer, streaming):
        self._producer = producer

    def unregisterProducer(self):
        self._producer = None

    def requestDone(self, _):
        pass

    def getPeer(self):
        return address.IPv4Address("TCP", "127.0.0.1", 0)

    def getHost(self):
        return address.IPv4Address("TCP", "127.0.0.1", 0)

    @property
    def transport(self):
        return self

    def getPeerCertificate(self):
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM.encode())

class FakeSite(Site):
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
        method_bytes = method.encode("utf-8")
    else:
        method_bytes = method
    if isinstance(path, text_type):
        path_bytes = path.encode("utf-8")
    else:
        path_bytes = path
    if shorthand and not path_bytes.startswith(b"/_matrix"):
        prefix = b"/_matrix/identity/v2/"
        if not path_bytes.startswith(b"/"):
            path_bytes = b"/" + path_bytes
        path_bytes = prefix + path_bytes.lstrip(b"/")
    if not path_bytes.startswith(b"/"):
        path_bytes = b"/" + path_bytes
    if isinstance(content, dict):
        body_bytes = json.dumps(content).encode("utf-8")
    elif isinstance(content, text_type):
        body_bytes = content.encode("utf-8")
    else:
        body_bytes = content
    site = FakeSite()
    channel = FakeChannel(site=site, _reactor=reactor)
    req = request(channel)
    req.process = lambda: b""
    req.content = BytesIO(body_bytes)
    req.postpath = [unquote(p) for p in path_bytes.split(b"/") if p]
    req.requestHeaders = Headers()
    if access_token is not None:
        token = access_token.encode("utf-8") if isinstance(access_token, text_type) else access_token
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + token)
    if federation_auth_origin is not None:
        origin = federation_auth_origin.encode("utf-8") if isinstance(federation_auth_origin, text_type) else federation_auth_origin
        req.requestHeaders.addRawHeader(b"Origin", origin)
    if body_bytes:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method_bytes, path_bytes, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    def __init__(self, formatter):
        super(ToTwistedHandler, self).__init__()
        self.logger = Logger()
        self.setFormatter(formatter)

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            if level == "warning":
                level = "warn"
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(msg)
        except Exception:
            self.handleError(record)

def setup_logging():
    root = logging.getLogger()
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)
    handler = ToTwistedHandler(formatter)
    root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR").upper()
    level = logging.getLevelName(level_name)
    if isinstance(level, str):
        level = logging.ERROR
    root.setLevel(level)