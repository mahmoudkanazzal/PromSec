import json
import logging
import os
from io import BytesIO
from typing import Any, Dict, Tuple, Optional
from dataclasses import dataclass, field
from six import text_type
from zope.interface import implementer
from twisted.internet._resolver import SimpleResolverComplexifier
from twisted.internet.defer import fail, succeed, Deferred
from twisted.internet.error import DNSLookupError
from twisted.internet.interfaces import IHostnameResolver, IReactorPluggableNameResolver, IResolverSimple
from twisted.internet import address
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto
from sydent.sydent import Sydent, parse_config_dict

FAKE_SERVER_CERT_PEM = ""

class ToTwistedHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record).replace("\n", "")
        record.msg = msg
        record.args = ()
        logger = logging.getLogger("ToTwistedHandler")
        logger.handle(record)

@implementer(IReactorPluggableNameResolver)
class ResolvingMemoryReactorClock(MemoryReactorClock):
    lookups: Dict[str, address.IPv4Address]

    def __init__(self) -> None:
        super().__init__()
        self.lookups = {}
        self.resolver = SimpleResolverComplexifier(self)

    def resolveHostName(self, hostname: str, timeout: Optional[int] = None) -> Deferred:
        if not isinstance(hostname, str):
            raise TypeError("hostname must be str")
        if hostname in self.lookups:
            return succeed(self.lookups[hostname])
        return fail(DNSLookupError())

    def installNameResolver(self, resolver: IResolverSimple) -> None:
        raise NotImplementedError()

    def getResolver(self) -> IResolverSimple:
        return self.resolver

@dataclass
class FakeChannel:
    json_body: bytes = b""
    code: int = 200
    headers: Dict[bytes, bytes] = field(default_factory=dict)

    def writeHeaders(self, headers: Dict[bytes, bytes]) -> None:
        if not isinstance(headers, dict):
            raise TypeError("headers must be dict")
        self.headers = headers

    def write(self, data: bytes) -> None:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")
        self.json_body += bytes(data)

    def registerProducer(self, producer: Any, streaming: bool) -> None:
        if not isinstance(streaming, bool):
            raise TypeError("streaming must be bool")

    def unregisterProducer(self) -> None:
        pass

    def requestDone(self) -> None:
        pass

    def getPeer(self) -> address.IPv4Address:
        return address.IPv4Address("127.0.0.1", 0)

    def getHost(self) -> address.IPv4Address:
        return address.IPv4Address("127.0.0.1", 0)

    @property
    def transport(self) -> Any:
        return self

    def getPeerCertificate(self) -> Any:
        return None

class FakeSite(Site):
    def __init__(self) -> None:
        super().__init__(resource=None)

def _create_safe_fake_channel(reactor: Any) -> FakeChannel:
    if not isinstance(reactor, IReactorPluggableNameResolver):
        raise TypeError("reactor must implement IReactorPluggableNameResolver")
    return FakeChannel()

def _to_bytes(value: Any, name: str) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, text_type):
        return value.encode("utf-8")
    raise TypeError(f"{name} must be bytes, bytearray, or text_type")

def make_request(
    method: Any,
    path: Any,
    access_token: Any,
    federation_auth_origin: Any,
    content: Any = None,
    shorthand: bool = False,
    reactor: Any = None,
    request: Any = Request,
) -> Tuple[Request, FakeChannel]:
    if not isinstance(shorthand, bool):
        raise TypeError("shorthand must be bool")
    method_b = _to_bytes(method, "method")
    path_b = _to_bytes(path, "path")
    token_b = _to_bytes(access_token, "access_token")
    origin_b = _to_bytes(federation_auth_origin, "federation_auth_origin")
    if shorthand and not path_b.startswith(b"/_matrix"):
        if not path_b.startswith(b"/"):
            path_b = b"/" + path_b
        path_b = b"/_matrix" + path_b
    if isinstance(content, dict):
        try:
            body_bytes = json.dumps(content).encode("utf-8")
        except Exception:
            body_bytes = b""
    elif isinstance(content, (bytes, bytearray)):
        body_bytes = bytes(content)
    elif isinstance(content, text_type):
        body_bytes = content.encode("utf-8")
    else:
        body_bytes = b""
    if not hasattr(reactor, "lookups"):
        raise TypeError("reactor must have a lookups attribute")
    channel = _create_safe_fake_channel(reactor)
    req_instance = request(channel)  # type: ignore[arg-type]
    req_instance.content = BytesIO(body_bytes)
    req_instance.requestHeaders = Headers()
    req_instance.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + token_b)
    req_instance.requestHeaders.addRawHeader(b"Origin", origin_b)
    if body_bytes:
        req_instance.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req_instance.requestReceived(method_b, path_b, b"1.1")
    return req_instance, channel

def make_sydent(test_config: Any = None) -> Sydent:
    if test_config is not None and not isinstance(test_config, dict):
        raise TypeError("test_config must be dict or None")
    config_dict = test_config if test_config is not None else {}
    config = parse_config_dict(config_dict)
    reactor = ResolvingMemoryReactorClock()
    syd = Sydent(config=config, reactor=reactor)  # type: ignore[arg-type]
    if hasattr(syd, "tls"):
        syd.tls = False
    return syd

def setup_logging() -> None:
    logger = logging.getLogger(__name__)
    logger.propagate = False
    level_str = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR")
    level = getattr(logging, level_str.upper(), logging.ERROR)
    logger.setLevel(level)
    handler = ToTwistedHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

if __name__ == "__main__":
    setup_logging()