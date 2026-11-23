import json
import os
import logging
from io import BytesIO
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple, Optional

import six
from zope.interface import implementer

from twisted.internet._resolver import SimpleResolverComplexifier
from twisted.internet.defer import fail, succeed
from twisted.internet.error import DNSLookupError
from twisted.internet.interfaces import IHostnameResolver, IReactorPluggableNameResolver, IResolverSimple
from twisted.internet.address import IPv4Address
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto
from sydent.sydent import Sydent, parse_config_dict

FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEbG9vZzANBgkqhkiG9w0BAQsFADBvMQswCQYDVQQGEwJV
UzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCk1vdW50YWluIFZpZXcxFjAUBgNVBAoT
DVNhbXBsZSBDb21wYW55MRUwEwYDVQQDEwxleGFtcGxlLmNvbTAeFw0yMTA1MDEw
MDAwMDBaFw0zMTA0MjkwMDAwMDBaMG8xCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJD
QTETMBEGA1UEBxMKTW91bnRhaW4gVmlldzEWMBQGA1UEChMNU2FtcGxlIENvbXBh
bnkxFTATBgNVBAMTDEXhhbXBsZS5jb20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAw
ggEKAoIBAQC7V6V6w5V6c5Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6
Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Z
c6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc
6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6
Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Z
c6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc
6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6
Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Z
c6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc
6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6
Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Z
c6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc
6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6
Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Z
c6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc
6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6
c6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc
6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6
c6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc
6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6
c6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc
6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6
c6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc6Zc
-----END CERTIFICATE-----"""

def make_sydent(test_config: Optional[Dict[str, Any]] = None) -> Sydent:
    cfg = parse_config_dict(test_config or {})
    reactor = ResolvingMemoryReactorClock()
    return Sydent(reactor=reactor, cfg=cfg, use_tls_for_federation=False)

@dataclass
class FakeChannel:
    site: Site
    _reactor: object
    result: Dict[str, Any] = field(default_factory=dict)
    _producer: Any = None
    producerStreaming: Any = None
    _body: BytesIO = field(default_factory=BytesIO)

    @property
    def json_body(self) -> Any:
        if not self.result:
            raise RuntimeError("Result not set")
        return self.result.get("json_body")

    @property
    def code(self) -> int:
        if not self.result:
            raise RuntimeError("Result not set")
        return self.result.get("code", 0)

    @property
    def headers(self) -> Dict[str, Any]:
        if not self.result:
            raise RuntimeError("Result not set")
        return self.result.get("headers", {})

    def writeHeaders(self, code: int, reason: bytes, headers: Headers) -> None:
        self.result["code"] = code
        self.result["headers"] = {k: v for k, v in headers.getAllRawHeaders()}

    def write(self, data: bytes) -> None:
        self._body.write(data)

    def registerProducer(self, producer: Any, streaming: bool) -> None:
        self._producer = producer
        self.producerStreaming = streaming

    def unregisterProducer(self) -> None:
        self._producer = None
        self.producerStreaming = None

    def requestDone(self, request: Request) -> None:
        body = self._body.getvalue()
        try:
            self.result["json_body"] = json.loads(body.decode("utf-8"))
        except Exception:
            self.result["json_body"] = body
        self._body.close()

    def getPeer(self) -> IPv4Address:
        return IPv4Address("TCP", "127.0.0.1", 0)

    def getHost(self) -> IPv4Address:
        return IPv4Address("TCP", "127.0.0.1", 0)

    @property
    def transport(self) -> Any:
        return self

    def getPeerCertificate(self) -> crypto.X509:
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM.encode())

class FakeSite(Site):
    pass

def make_request(
    reactor: Any,
    method: Any,
    path: Any,
    content: Any = b"",
    access_token: Optional[str] = None,
    request: Any = Request,
    shorthand: bool = True,
    federation_auth_origin: Optional[str] = None,
) -> Tuple[Request, FakeChannel]:
    if isinstance(method, six.text_type):
        method = method.encode("utf-8")
    if isinstance(path, six.text_type):
        path = path.encode("utf-8")
    if shorthand and not path.startswith(b"/_matrix"):
        path = b"/_matrix/identity/v2/" + path.lstrip(b"/")
    if not path.startswith(b"/"):
        path = b"/" + path
    if isinstance(content, dict):
        content = json.dumps(content).encode("utf-8")
    elif isinstance(content, six.text_type):
        content = content.encode("utf-8")
    site = FakeSite(reactor=reactor)
    channel = FakeChannel(site=site, _reactor=reactor)
    req = request(channel)
    req.process = lambda: succeed(b"")
    req.content = BytesIO(content)
    raw_path = path.lstrip(b"/")
    segments = [unquote(seg) for seg in raw_path.split(b"/") if seg]
    req.postpath = segments
    if access_token:
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + access_token.encode())
    if federation_auth_origin:
        req.requestHeaders.addRawHeader(b"Origin", federation_auth_origin.encode())
    if content:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method, path, b"1.1")
    return req, channel

def setup_logging() -> None:
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR")
    level = getattr(logging, level_name.upper(), logging.ERROR)
    logger = logging.getLogger()
    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(handler)

setup_logging()

@implementer(IReactorPluggableNameResolver)
class ResolvingMemoryReactorClock(MemoryReactorClock):
    def __init__(self) -> None:
        self.lookups: Dict[str, str] = {}
        class FakeResolver:
            implements = IResolverSimple
            def getHostByName(self, name: str, timeout: Optional[int] = None):
                if name not in self.lookups:
                    return fail(DNSLookupError(f"Hostname {name} not found"))
                return succeed(self.lookups[name])
        self.nameResolver = SimpleResolverComplexifier(FakeResolver())
        super().__init__()

    def installNameResolver(self, resolver: IHostnameResolver) -> IHostnameResolver:
        raise NotImplementedError()