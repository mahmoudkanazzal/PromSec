import json
import logging
import os
from io import BytesIO

import attr
from six import text_type
from twisted.internet import address as twisted_address
from twisted.logger import Logger, LogLevel
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
BQADggEPADCCAQoCggEBAL6V6V6K5vZc6K6c5Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6
Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Z
-----END CERTIFICATE-----"""

def _to_ascii_bytes(value, name):
    if not isinstance(value, text_type):
        raise TypeError(f"{name} must be a text_type, got {type(value).__name__}")
    try:
        return value.encode("ascii")
    except UnicodeEncodeError as e:
        raise ValueError(f"{name} contains non‑ASCII characters") from e

def _sanitize_header_value(value):
    return value.replace(b"\r", b"").replace(b"\n", b"")

def make_sydent(test_config=None):
    cfg = {}
    if test_config:
        cfg.update(test_config)
    cfg.setdefault("db.file", ":memory:")
    reactor = MemoryReactorClock()
    return Sydent(reactor, parse_config_dict(cfg))

@attr.s
class FakeChannel:
    site = attr.ib()
    _reactor = attr.ib()
    result = attr.ib(factory=dict)
    _producer = attr.ib(default=None)

    @property
    def json_body(self):
        body = self.result.get("body")
        if body is None:
            raise KeyError("body not found in result")
        return json.loads(body.decode("utf-8"))

    @property
    def code(self):
        return self.result["code"]

    @property
    def headers(self):
        return Headers(self.result["headers"])

    def writeHeaders(self, code, headers):
        self.result["code"] = code
        self.result["headers"] = dict(headers.getAllRawHeaders())

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
        return twisted_address.IPv4Address("TCP", "127.0.0.1", 12345)

    def getHost(self):
        return twisted_address.IPv4Address("TCP", "127.0.0.1", 80)

    @property
    def transport(self):
        return self

    def getPeerCertificate(self):
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM.encode("utf-8"))

class FakeSite:
    pass

def make_request(reactor, method, path, content=b"", access_token=None, request=Request, shorthand=True, federation_auth_origin=None):
    if isinstance(method, bytes):
        method_bytes = method
    else:
        method_bytes = _to_ascii_bytes(method, "method")
    if isinstance(path, bytes):
        path_bytes = path
    else:
        path_bytes = _to_ascii_bytes(path, "path")
    if shorthand and not path_bytes.startswith(b"/_matrix"):
        path_bytes = b"/_matrix/identity/v2/" + path_bytes.lstrip(b"/")
    while b"//" in path_bytes:
        path_bytes = path_bytes.replace(b"//", b"/")
    if not path_bytes.startswith(b"/"):
        path_bytes = b"/" + path_bytes
    if isinstance(content, dict):
        body_bytes = json.dumps(content).encode("utf-8")
    elif isinstance(content, text_type):
        body_bytes = content.encode("utf-8")
    elif isinstance(content, (bytes, bytearray)):
        body_bytes = bytes(content)
    else:
        body_bytes = b""
    site = FakeSite()
    channel = FakeChannel(site=site, _reactor=reactor)
    req = request(channel)
    req.requestHeaders = Headers()
    req.process = lambda: b""
    req.content = BytesIO(body_bytes)
    req.postpath = [unquote(seg) for seg in path_bytes.split(b"/") if seg]
    if access_token is not None:
        token = _sanitize_header_value(access_token.encode("utf-8"))
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + token)
    if federation_auth_origin is not None:
        origin = _sanitize_header_value(federation_auth_origin.encode("utf-8"))
        auth_value = b"X-Matrix origin=%s,key=,sig=" % origin
        req.requestHeaders.addRawHeader(b"Authorization", auth_value)
    if body_bytes:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method_bytes, path_bytes, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logger = Logger()

    def emit(self, record):
        try:
            msg = self.format(record)
            level_name = record.levelname.lower()
            if level_name == "warning":
                level = LogLevel.warn
            else:
                level = getattr(LogLevel, level_name, LogLevel.info)
            self.logger.emit(message=msg, logLevel=level)
        except Exception:
            self.logger.emit(message=self.format(record), logLevel=LogLevel.info)

def setup_logging():
    root = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s")
    handler = ToTwistedHandler()
    handler.setFormatter(formatter)
    root.addHandler(handler)
    level_str = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR").upper()
    valid_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
    if level_str not in valid_levels:
        level = logging.ERROR
    else:
        level = getattr(logging, level_str, logging.ERROR)
    root.setLevel(level)

setup_logging()