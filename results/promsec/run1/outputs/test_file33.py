import json
import os
from io import BytesIO
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Tuple, Optional, Dict, Union

import six
from zope.interface import implementer

from twisted.internet._resolver import SimpleResolverComplexifier
from twisted.internet.defer import fail, succeed
from twisted.internet.error import DNSLookupError
from twisted.internet.interfaces import IHostnameResolver, IReactorPluggableNameResolver, IResolverSimple
from twisted.internet import address
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
DVN5c3RlbSBJbmMuMRUwEwYDVQQDEwxleGFtcGxlLmNvbTAeFw0yMTA1MDEwMDAw
MDBaFw0zMTA0MjkwMDAwMDBaMG8xCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJDQTET
MBEGA1UEBxMKTW91bnRhaW4gVmlldzEWMBQGA1UEChMNU3lzdGVtIEluYy4xFTAT
BgNVBAMTDGV4YW1wbGUuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKC
AQEAxV6K6wX6Z1GDZCBoBPXaG9q4CPGK/c/pX9nuSUXwxLBzME2YkdE+5EYXPLk6
2b7xvFeoJEB6Digw1k3D6Z0SqnX+0Gooy2cwr6jciJ6TP2PzefRg2fzGEGZm4G6E
nr5lTyBC0bYKT1eZq9VHtV6nRvWmvMRGsiE9z1FMvx6bMpiKFFitvolG/G5hgbfG
Q5e0M1Vo9hw3rroWAtxEvsC0BpvyEukgqS0bkkCm1cW0XkyRjO6jwxKF1u9IiMaB
99ZTSdK6Ff8gDuwZQzQ0jrISFRCGDpa2BkLomqKgJo0vvVuv5AO9M/dwZ0pniS3p
DOMkMt2rt7NmBGG99nmCaTKtyQIDAQABo1AwTjAdBgNVHQ4EFgQUaKBslZx2drXr
I8o1gChX2NDVYWMwHwYDVR0jBBgwFoAUaKBslZx2drXrI8o1gChX2NDVYWMwDAYD
VR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAAI6Bfq5lHppZArYdS9x+h0cY
jfbQ3VIAtF5NCz7L+G5kZZgwyU0YJIUKGwEuITdSb9VjA36TObgGJE0E7E5Wdl66
RS0LlwM1c01qmPvvrLpzjAU6YewsGQKzBSSMSmc5QwDFi1Cdm42Hcps225y7sY9V
0kGugHgd6NqBJ38qRAjPR9U1FVLtZL1NVr7Di5urN6byN1Nsx3Rp3XIan+FJxux1
ZWS9Vyuk3F7S3w7Dnk3a1JpN96CB2A+qsYqSdz+CA0nVddOZXS6jttuPAHyBs+K6
nDz3jAC5vVsQt1zArhcXd1LSeXfhBF3/f6/Dr7guP5AnbcW2CYwiVdc+GQ==
-----END CERTIFICATE-----"""

@implementer(IReactorPluggableNameResolver)
class ResolvingMemoryReactorClock(MemoryReactorClock):
    def __init__(self) -> None:
        self.lookups: Dict[str, str] = {}
        class FakeResolver:
            implements = IResolverSimple
            def __init__(self, outer: "ResolvingMemoryReactorClock"):
                self._outer = outer
            def getHostByName(self, name: str, timeout: Optional[int] = None):
                if name not in self._outer.lookups:
                    return fail(DNSLookupError(f"DNS lookup failed for {name}"))
                return succeed(self._outer.lookups[name])
        self.nameResolver = SimpleResolverComplexifier(FakeResolver(self))
        super().__init__()
    def installNameResolver(self, resolver: IHostnameResolver) -> IHostnameResolver:
        raise NotImplementedError

def make_sydent(test_config: Optional[Dict[str, Any]] = None) -> Sydent:
    cfg = test_config.copy() if test_config else {}
    cfg.setdefault("db.file", ":memory:")
    parsed_cfg = parse_config_dict(cfg)
    reactor = ResolvingMemoryReactorClock()
    return Sydent(reactor=reactor, cfg=parsed_cfg, use_tls_for_federation=False)

@dataclass
class FakeChannel:
    site: Site
    _reactor: Any
    result: Dict[str, Any] = field(default_factory=dict)
    _producer: Any = None
    producerStreaming: Any = None
    @property
    def json_body(self) -> Any:
        if not self.result:
            raise RuntimeError("Result is empty")
        return json.loads(self.result["body"].decode("utf-8"))
    @property
    def code(self) -> int:
        if not self.result:
            raise RuntimeError("Result is empty")
        return int(self.result["code"])
    @property
    def headers(self) -> Headers:
        if not self.result:
            raise RuntimeError("Result is empty")
        return Headers(self.result["headers"])
    def writeHeaders(self, version: bytes, code: int, reason: bytes, headers: Dict[bytes, list[bytes]]) -> None:
        self.result["version"] = version
        self.result["code"] = code
        self.result["reason"] = reason
        self.result["headers"] = {k.decode(): [v.decode() for v in vals] for k, vals in headers.items()}
    def write(self, content: bytes) -> None:
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError("Content must be bytes")
        self.result["body"] = self.result.get("body", b"") + content
    def registerProducer(self, producer: Any, streaming: bool) -> None:
        self._producer = producer
        self.producerStreaming = streaming
        delay = 0 if streaming else 0.1
        self._reactor.callLater(delay, producer.resumeProducing)
    def unregisterProducer(self) -> None:
        self._producer = None
        self.producerStreaming = None
    def requestDone(self, _self: Any) -> None:
        self.result["done"] = True
    def getPeer(self) -> address.IPv4Address:
        return address.IPv4Address("TCP", "127.0.0.1", 3423)
    def getHost(self) -> None:
        return None
    @property
    def transport(self) -> "FakeChannel":
        return self
    def getPeerCertificate(self) -> crypto.X509:
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM.encode())

class FakeSite(Site):
    pass

def make_request(
    reactor: Any,
    method: Union[bytes, str],
    path: Union[bytes, str],
    content: Union[bytes, dict, six.text_type] = b"",
    access_token: Optional[str] = None,
    request: Callable[..., Request] = Request,
    shorthand: bool = True,
    federation_auth_origin: Optional[str] = None,
) -> Tuple[Request, FakeChannel]:
    if isinstance(method, str):
        method = method.encode("ascii")
    if isinstance(path, str):
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
    req.requestHeaders = Headers({})
    if access_token is not None:
        req.requestHeaders.addRawHeader("Authorization", f"Bearer {access_token}")
    if federation_auth_origin is not None:
        req.requestHeaders.addRawHeader("Authorization", f"X-Matrix origin={federation_auth_origin},key=,sig=")
    if content:
        req.requestHeaders.addRawHeader("Content-Type", "application/json")
    req.requestReceived(method, path, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    tx_log = Logger()
    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        level_name = record.levelname.lower()
        if level_name == "warning":
            level_name = "warn"
        level = LogLevel.levelWithName(level_name)
        self.tx_log.emit(message=msg, log_level=level)

def setup_logging() -> None:
    root = logging.getLogger()
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    handler = ToTwistedHandler()
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR")
    root.setLevel(level_name.upper())

setup_logging()