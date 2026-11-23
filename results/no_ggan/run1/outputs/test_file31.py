import json
import logging
import os
from io import BytesIO
from typing import Dict, Optional, Any
import attr
from six import text_type
from zope.interface import implementer
from twisted.internet._resolver import SimpleResolverComplexifier
from twisted.internet.defer import fail, succeed, Deferred
from twisted.internet.error import DNSLookupError
from twisted.internet.interfaces import IHostnameResolver, IReactorPluggableNameResolver, IResolverSimple
from twisted.internet import address
from twisted.logger import Logger
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

def make_sydent(test_config: Optional[Dict] = None) -> Sydent:
    """
    Create a Sydent instance with an in‑memory SQLite database and a
    ResolvingMemoryReactorClock. TLS for federation is disabled.
    """
    if test_config is None:
        test_config = {
            "sydent": {
                "db": "sqlite:///:memory:",
                "use_tls_for_federation": "false",
            }
        }
    config = parse_config_dict(test_config)
    reactor = ResolvingMemoryReactorClock()
    sydent = Sydent(config, reactor=reactor)
    sydent.use_tls_for_federation = False
    return sydent

@attr.s
class FakeChannel:
    """
    A minimal channel used for testing Twisted Request handling.
    """
    site = attr.ib()
    _reactor = attr.ib()
    result = attr.ib(factory=dict)
    _producer = attr.ib(default=None)

    @property
    def json_body(self) -> Any:
        if not self.result:
            raise RuntimeError("No result available")
        return json.loads(self.result.get("body", b"").decode("utf-8"))

    @property
    def code(self) -> int:
        if not self.result:
            raise RuntimeError("No result available")
        return self.result.get("code", 0)

    @property
    def headers(self) -> Headers:
        if not self.result:
            raise RuntimeError("No result available")
        return self.result.get("headers", Headers())

    def writeHeaders(self, code: int, message: bytes, headers: Headers) -> None:
        self.result["code"] = code
        self.result["message"] = message
        self.result["headers"] = headers

    def write(self, data: bytes) -> None:
        body = self.result.get("body", b"")
        self.result["body"] = body + data

    def registerProducer(self, producer: Any, streaming: bool) -> None:
        self._producer = producer

    def unregisterProducer(self) -> None:
        self._producer = None

    def requestDone(self, _ignored: Any = None) -> None:
        pass

    def getPeer(self) -> address.IPv4Address:
        return address.IPv4Address("127.0.0.1", 0)

    def getHost(self) -> address.IPv4Address:
        return address.IPv4Address("127.0.0.1", 0)

    @property
    def transport(self) -> "FakeChannel":
        return self

    def getPeerCertificate(self) -> crypto.X509:
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM.encode("utf-8"))

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
) -> tuple:
    """
    Build a Twisted Request and associated FakeChannel for testing.
    """
    if isinstance(method, text_type):
        method_bytes = method.encode("utf-8")
    elif isinstance(method, bytes):
        method_bytes = method
    else:
        raise TypeError("method must be str or bytes")
    if isinstance(path, text_type):
        path_bytes = path.encode("utf-8")
    elif isinstance(path, bytes):
        path_bytes = path
    else:
        raise TypeError("path must be str or bytes")
    if shorthand:
        prefix = b"/_matrix/identity/v2"
        if not path_bytes.startswith(b"/"):
            path_bytes = b"/" + path_bytes
        path_bytes = prefix + path_bytes
    if not path_bytes.startswith(b"/"):
        path_bytes = b"/" + path_bytes
    if isinstance(content, dict):
        body_bytes = json.dumps(content).encode("utf-8")
    elif isinstance(content, text_type):
        body_bytes = content.encode("utf-8")
    elif isinstance(content, bytes):
        body_bytes = content
    else:
        raise TypeError("content must be dict, str, or bytes")
    site = FakeSite()
    channel = FakeChannel(site=site, _reactor=reactor)
    req = request(channel, False)
    req.process = lambda: b""
    req.content = BytesIO(body_bytes)
    stripped = path_bytes.lstrip(b"/")
    req.postpath = [unquote(p) for p in stripped.split(b"/") if p]
    if access_token is not None:
        auth = b"Bearer " + access_token.encode("utf-8")
        req.requestHeaders.addRawHeader(b"Authorization", auth)
    if body_bytes:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method_bytes, path_bytes, b"HTTP/1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    """
    Logging handler that forwards records to Twisted's logger.
    """
    def __init__(self) -> None:
        super().__init__()
        self._logger = Logger()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            if level == "warning":
                level = "warn"
            log_method = getattr(self._logger, level, self._logger.error)
            log_method(msg)
        except Exception:
            self.handleError(record)

def _resolve_log_level(name: str) -> int:
    """
    Resolve a log level name to a numeric level, defaulting to ERROR.
    """
    try:
        return logging._nameToLevel[name.upper()]
    except Exception:
        return logging.ERROR

def setup_logging() -> None:
    """
    Configure root logger to use ToTwistedHandler and environment level.
    """
    root = logging.getLogger()
    root.handlers = []
    handler = ToTwistedHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR")
    root.setLevel(_resolve_log_level(level_name))

setup_logging()

@implementer(IReactorPluggableNameResolver)
class ResolvingMemoryReactorClock(MemoryReactorClock):
    """
    MemoryReactorClock with a simple name resolver for testing.
    """
    def __init__(self) -> None:
        self.lookups: Dict[str, str] = {}
        class FakeResolver:
            implements = IResolverSimple
            def __init__(self, parent: "ResolvingMemoryReactorClock"):
                self._parent = parent
            def getHostByName(self, name: str, timeout: Optional[int] = None) -> Deferred:
                if name in self._parent.lookups:
                    return succeed(self._parent.lookups[name])
                return fail(DNSLookupError())
        self.nameResolver = SimpleResolverComplexifier(FakeResolver(self))
        super().__init__()

    def installNameResolver(self, resolver: IHostnameResolver) -> IHostnameResolver:
        raise NotImplementedError()