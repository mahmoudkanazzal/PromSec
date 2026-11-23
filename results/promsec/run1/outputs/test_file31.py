import json
import os
from io import BytesIO
import logging
from dataclasses import dataclass, field

import six
from zope.interface import implementer
from twisted.internet._resolver import SimpleResolverComplexifier
from twisted.internet.defer import fail, succeed
from twisted.internet.error import DNSLookupError
from twisted.internet.interfaces import IHostnameResolver, IReactorPluggableNameResolver, IResolverSimple
from twisted.internet.address import IPv4Address
from twisted.logger import Logger, LogLevel
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto
from sydent.sydent import Sydent, parse_config_dict

FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEbG9nZzANBgkqhkiG9w0BAQsFADBoMQswCQYDVQQGEwJV
UzELMAkGA1UECBMCQ0ExEDAOBgNVBAcTB0JlcmtlbGV5MRAwDgYDVQQKEwdFeGFt
cGxlMRAwDgYDVQQLEwdFeGFtcGxlMRMwEQYDVQQDEwpFeGFtcGxlIENBMB4XDTIx
MDkwMTAwMDAwMFoXDTMxMDgyOTAwMDAwMFowaDELMAkGA1UEBhMCVVMxCzAJBgNV
BAgTAkNBMRAwDgYDVQQHEwdCZXJrZWxleTEQMA4GA1UEChMHRXhhbXBsZTEQMA4G
A1UECxMHRXhhbXBsZTESMBAGA1UEAxMJbG9jYWxob3N0MIIBIjANBgkqhkiG9w0B
AQEFAAOCAQ8AMIIBCgKCAQEArV6V6wX+Z1ZL+6K5eZc+6Zc6c5V6Z6c5V6Z6c5V
6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c
5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z
6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5V
6Z6c5V6Z6c5V6Z6c5V6Z6c5V6Z6c5VwIDAQAB
-----END CERTIFICATE-----"""

def make_sydent(test_config: dict | None = None) -> Sydent:
    cfg = {}
    if test_config:
        cfg.update(test_config)
    cfg.setdefault("db.file", ":memory:")
    parsed_cfg = parse_config_dict(cfg)
    reactor = ResolvingMemoryReactorClock()
    return Sydent(reactor=reactor, cfg=parsed_cfg, use_tls_for_federation=False)

@dataclass
class FakeChannel:
    site: Site
    _reactor: any
    result: dict = field(default_factory=dict)
    _producer: any = None
    producerStreaming: any = None

    @property
    def json_body(self):
        if not self.result or "body" not in self.result:
            raise Exception("No result body")
        return json.loads(self.result["body"].decode("utf-8"))

    @property
    def code(self):
        if not self.result or "code" not in self.result:
            raise Exception("No result code")
        return int(self.result["code"])

    @property
    def headers(self):
        if not self.result or "headers" not in self.result:
            raise Exception("No result headers")
        hdrs = Headers()
        for k, v in self.result["headers"].items():
            hdrs.addRawHeader(k, v)
        return hdrs

    def writeHeaders(self, version, code, reason, headers):
        self.result["version"] = version
        self.result["code"] = code
        self.result["reason"] = reason
        self.result["headers"] = dict(headers)

    def write(self, content):
        if not isinstance(content, bytes):
            raise TypeError("Content must be bytes")
        self.result.setdefault("body", b"")
        self.result["body"] += content

    def registerProducer(self, producer, streaming):
        self._producer = producer
        self.producerStreaming = streaming
        def _resume():
            if self._producer is not None:
                self._producer.resumeProducing()
                self._reactor.callLater(0.1, _resume)
        if streaming:
            self._reactor.callLater(0, self._producer.resumeProducing)
        else:
            self._reactor.callLater(0.1, _resume)

    def unregisterProducer(self):
        self._producer = None
        self.producerStreaming = None

    def requestDone(self, _self):
        self.result["done"] = True

    def getPeer(self):
        return IPv4Address("TCP", "127.0.0.1", 3423)

    def getHost(self):
        return None

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
) -> tuple[Request, FakeChannel]:
    if not isinstance(method, (bytes, bytearray)):
        method = method.encode("ascii")
    if not isinstance(path, (bytes, bytearray)):
        path = path.encode("ascii")
    if shorthand and not path.startswith(b"/_matrix"):
        path = b"/_matrix/identity/v2/" + path.lstrip(b"/")
        while b"//" in path:
            path = path.replace(b"//", b"/")
    if not path.startswith(b"/"):
        path = b"/" + path
    if isinstance(content, dict):
        content = json.dumps(content).encode("utf-8")
    elif isinstance(content, six.text_type):
        content = content.encode("utf-8")
    site = FakeSite()
    channel = FakeChannel(site=site, _reactor=reactor)
    req = request(channel)
    req.process = lambda: b""
    req.content = BytesIO(content)
    req.postpath = [unquote(p) for p in path.lstrip(b"/").split(b"/")]
    req.requestHeaders = Headers()
    if access_token is not None:
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + access_token.encode())
    if federation_auth_origin is not None:
        header = b"X-Matrix origin=" + federation_auth_origin.encode() + b",key=,sig="
        req.requestHeaders.addRawHeader(b"Authorization", header)
    if content:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method, path, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    tx_log = Logger()
    def emit(self, record):
        msg = self.format(record)
        level_name = record.levelname.lower().replace("warning", "warn")
        log_level = LogLevel.levelWithName(level_name)
        self.tx_log.emit(message=msg, log_level=log_level)

def setup_logging():
    root = logging.getLogger()
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    handler = ToTwistedHandler()
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)
    level = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR")
    root.setLevel(level)

setup_logging()

@implementer(IReactorPluggableNameResolver)
class ResolvingMemoryReactorClock(MemoryReactorClock):
    def __init__(self):
        self.lookups: dict[str, str] = {}
        class FakeResolver:
            def __init__(self, outer):
                self.outer = outer
            def getHostByName(self, name, timeout=None):
                if name not in self.outer.lookups:
                    return fail(DNSLookupError(f"Name {name} not found"))
                return succeed(self.outer.lookups[name])
        self.nameResolver = SimpleResolverComplexifier(FakeResolver(self))
        super().__init__()
    def installNameResolver(self, resolver: IHostnameResolver) -> IHostnameResolver:
        raise NotImplementedError