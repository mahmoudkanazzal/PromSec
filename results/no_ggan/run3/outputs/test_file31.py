import json
import logging
import os
from io import BytesIO
from typing import Dict, Optional

import attr
import six
from twisted.internet._resolver import SimpleResolverComplexifier
from twisted.internet.defer import fail, succeed
from twisted.internet.error import DNSLookupError
from twisted.internet.interfaces import IHostnameResolver, IReactorPluggableNameResolver, IResolverSimple
from twisted.internet import address
from twisted.logger import Logger
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto
from zope.interface import implementer

from sydent.sydent import Sydent, parse_config_dict

FAKE_SERVER_CERT_PEM = """
-----BEGIN CERTIFICATE-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArV6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK
6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V
6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J6ZcK6V6V6K6J
-----END CERTIFICATE-----
"""

def make_sydent(test_config: Optional[Dict] = None) -> Sydent:
    base_config = {"db": {"file": ":memory:"}}
    if test_config:
        base_config.update(test_config)
    config = parse_config_dict(base_config)
    reactor = ResolvingMemoryReactorClock()
    return Sydent(reactor=reactor, config=config, use_tls_for_federation=False)

@attr.s
class FakeChannel:
    site = attr.ib()
    _reactor = attr.ib()
    result = attr.ib(factory=dict)
    _producer = attr.ib(default=None)

    @property
    def json_body(self):
        if not self.result:
            raise RuntimeError("Result is empty")
        body = self.result.get("body", b"")
        if not isinstance(body, (bytes, bytearray)):
            raise TypeError("Body is not bytes")
        return json.loads(body.decode("utf-8"))

    @property
    def code(self):
        if not self.result:
            raise RuntimeError("Result is empty")
        return int(self.result.get("code", 0))

    @property
    def headers(self):
        if not self.result:
            raise RuntimeError("Result is empty")
        hdrs = self.result.get("headers", [])
        return Headers(hdrs)

    def writeHeaders(self, hdrs):
        if not isinstance(hdrs, list):
            raise TypeError("Headers must be a list of tuples")
        self.result["headers"] = [(k, v) for k, v in hdrs]

    def write(self, data):
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Data must be bytes")
        self.result.setdefault("body", b"")
        self.result["body"] += data

    def registerProducer(self, producer, streaming):
        self._producer = producer

    def unregisterProducer(self):
        self._producer = None

    def requestDone(self, _):
        self.result["done"] = True

    def getPeer(self):
        return address.IPv4Address("TCP", "127.0.0.1", 12345)

    def getHost(self):
        return address.IPv4Address("TCP", "127.0.0.1", 12345)

    @property
    def transport(self):
        return self

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
    if isinstance(method, six.text_type):
        method_bytes = method.encode("ascii", "ignore")
    elif isinstance(method, bytes):
        method_bytes = method
    else:
        raise TypeError("Method must be str or bytes")
    method_bytes = method_bytes.upper()

    if isinstance(path, six.text_type):
        path_bytes = path.encode("ascii", "ignore")
    elif isinstance(path, bytes):
        path_bytes = path
    else:
        raise TypeError("Path must be str or bytes")
    if shorthand and not path_bytes.startswith(b"/_matrix"):
        prefix = b"/_matrix/identity/v2/"
        if not path_bytes.startswith(b"/"):
            path_bytes = b"/" + path_bytes
        path_bytes = prefix + path_bytes.lstrip(b"/")
    if not path_bytes.startswith(b"/"):
        path_bytes = b"/" + path_bytes.lstrip(b"/")

    if isinstance(content, dict):
        body_bytes = json.dumps(content).encode("utf-8")
    elif isinstance(content, six.text_type):
        body_bytes = content.encode("utf-8")
    elif isinstance(content, bytes):
        body_bytes = content
    else:
        raise TypeError("Content must be dict, str, or bytes")

    site = FakeSite()
    channel = FakeChannel(site=site, _reactor=reactor)
    req = request(channel, False)
    req.process = lambda: None
    req.content = BytesIO(body_bytes)
    req.postpath = [unquote(p) for p in path_bytes.split(b"/")[1:] if p]

    if access_token is not None:
        token = six.text_type(access_token).encode("ascii", "ignore")
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + token)

    if federation_auth_origin is not None:
        origin = six.text_type(federation_auth_origin).encode("ascii", "ignore")
        auth_value = b"X-Matrix origin=" + origin + b",key=,sig="
        req.requestHeaders.addRawHeader(b"Authorization", auth_value)

    if body_bytes:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")

    req.requestReceived(method_bytes, path_bytes, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.tx_log = Logger()

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            if level == "warning":
                level = "warn"
            emit_func = getattr(self.tx_log, level, self.tx_log.info)
            emit_func(msg)
        except Exception:
            self.handleError(record)

def _resolve_log_level(level_name: str) -> int:
    name = level_name.upper()
    mapping = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return mapping.get(name, logging.ERROR)

def setup_logging():
    root = logging.getLogger()
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)
    handler = ToTwistedHandler()
    handler.setFormatter(formatter)
    root.handlers = []
    root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR")
    root.setLevel(_resolve_log_level(level_name))

setup_logging()

@implementer(IReactorPluggableNameResolver)
class ResolvingMemoryReactorClock(MemoryReactorClock):
    def __init__(self):
        super().__init__()
        self.lookups = {}

        class FakeResolver:
            @implementer(IResolverSimple)
            def getHostByName(inner_self, name, timeout=None):
                if name in self.lookups:
                    return succeed(self.lookups[name])
                return fail(DNSLookupError(f"Unknown host: {name}"))

        self.nameResolver = SimpleResolverComplexifier(FakeResolver())

    def installNameResolver(self, resolver):
        raise NotImplementedError("installNameResolver is not supported")