import json
import logging
import os
from io import BytesIO
from typing import Any, Dict, Tuple, Optional, Union

import attr
from six import text_type
from twisted.internet._resolver import SimpleResolverComplexifier
from twisted.internet.defer import fail, succeed
from twisted.internet.error import DNSLookupError
from twisted.internet.interfaces import IHostnameResolver, IReactorPluggableNameResolver, IResolverSimple
from twisted.internet.address import IPv4Address
from twisted.logger import Logger as TwistedLogger
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto
from zope.interface import implementer

from sydent.sydent import Sydent, parse_config_dict


def _validate_log_level(level_name: str) -> int:
    """Normalize and validate a log level name."""
    normalized = level_name.upper()
    mapping = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return mapping.get(normalized, logging.ERROR)


class ToTwistedHandler(logging.Handler):
    """Logging handler that forwards records to Twisted's logger."""

    _twisted_logger = TwistedLogger()

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        level = record.levelname.lower()
        if level == "warning":
            level = "warn"
        emit_method = getattr(self._twisted_logger, level, self._twisted_logger.error)
        emit_method(msg)


def setup_logging() -> None:
    """Configure root logger to forward to Twisted logger."""
    root = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s")
    handler = ToTwistedHandler()
    handler.setFormatter(formatter)
    root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR")
    root.setLevel(_validate_log_level(level_name))


setup_logging()


@implementer(IReactorPluggableNameResolver)
class ResolvingMemoryReactorClock(MemoryReactorClock):
    """Memory reactor with a simple DNS resolver."""

    def __init__(self) -> None:
        self.lookups: Dict[str, str] = {}

        @implementer(IResolverSimple)
        class FakeResolver:
            def __init__(self, outer: "ResolvingMemoryReactorClock") -> None:
                self._outer = outer

            def getHostByName(self, name: str, timeout: Optional[int] = None) -> Any:
                if name not in self._outer.lookups:
                    return fail(DNSLookupError(f"Name {name} not found"))
                return succeed(self._outer.lookups[name])

        self.nameResolver = SimpleResolverComplexifier(FakeResolver(self))
        super().__init__()

    def installNameResolver(self, resolver: IHostnameResolver) -> IHostnameResolver:
        raise NotImplementedError


@attr.s(auto_attribs=True, slots=True)
class FakeChannel:
    """A minimal channel implementation for testing."""

    reactor: Any
    _code: Optional[int] = None
    _headers: Optional[Headers] = None
    _body: BytesIO = attr.ib(factory=BytesIO)

    @property
    def code(self) -> int:
        if self._code is None:
            raise RuntimeError("Response code not set")
        return self._code

    @property
    def headers(self) -> Headers:
        if self._headers is None:
            raise RuntimeError("Headers not set")
        return self._headers

    @property
    def json_body(self) -> Any:
        if self._body.getbuffer().nbytes == 0:
            raise RuntimeError("No body received")
        try:
            return json.loads(self._body.getvalue().decode("utf-8"))
        except Exception as e:
            raise RuntimeError("Invalid JSON body") from e

    def writeHeaders(self, code: int, headers: Headers) -> None:
        self._code = code
        self._headers = headers

    def write(self, data: bytes) -> None:
        if not isinstance(data, (bytes, bytearray)):
            raise AssertionError("write expects bytes")
        self._body.write(data)

    def registerProducer(self, producer: Any, streaming: bool) -> None:
        if streaming:
            self.reactor.callLater(0, getattr(producer, "resumeProducing", lambda: None))
        else:
            stop = getattr(producer, "stopProducing", None)
            if callable(stop):
                stop()

    def unregisterProducer(self) -> None:
        pass

    def requestDone(self, _ignored: Any = None) -> None:
        pass

    def getPeer(self) -> IPv4Address:
        return IPv4Address("TCP", "127.0.0.1", 0)

    def getHost(self) -> IPv4Address:
        return IPv4Address("TCP", "127.0.0.1", 0)

    @property
    def transport(self) -> Any:
        return self

    def getPeerCertificate(self) -> crypto.X509:
        pem = b"""-----BEGIN CERTIFICATE-----
MIIBtjCCAVugAwIBAgIJAO6V6V6cKc2VMA0GCSqGSIb3DQEBCwUAMBQxEjAQBgNV
BAMTCWxvY2FsaG9zdDAeFw0yMTA0MDYxNzI5MzNaFw0zMTA0MDQxNzI5MzNaMBQx
EjAQBgNVBAMTCWxvY2FsaG9zdDCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEA
xV6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK
6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK
6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK
6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK
6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK
6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK
6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK
6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK6V6cK
-----END CERTIFICATE-----"""
        return crypto.load_certificate(crypto.FILETYPE_PEM, pem)


class FakeSite:
    """Placeholder for Twisted Site."""

    def __init__(self, resource: Any) -> None:
        self.resource = resource

    def log(self, *args: Any, **kwargs: Any) -> None:
        pass


def make_sydent(test_config: Optional[Dict[str, Any]] = None) -> Sydent:
    """
    Create a Sydent instance for testing.

    Args:
        test_config: Optional configuration dictionary.

    Returns:
        Configured Sydent instance.
    """
    config_dict = dict(test_config or {})
    db_conf = config_dict.setdefault("db", {})
    db_conf.setdefault("file", ":memory:")
    parsed_config = parse_config_dict(config_dict)
    reactor = ResolvingMemoryReactorClock()
    return Sydent(reactor=reactor, config=parsed_config, use_tls_for_federation=False)


def make_request(
    reactor: Any,
    method: Union[bytes, str],
    path: Union[bytes, str],
    content: Union[bytes, str, Dict[str, Any]] = b"",
    access_token: Optional[str] = None,
    request: Any = Request,
    shorthand: bool = True,
    federation_auth_origin: Optional[str] = None,
) -> Tuple[Request, FakeChannel]:
    """
    Build a fake HTTP request for testing.

    Returns:
        Tuple of (Request, FakeChannel).
    """
    if isinstance(method, str):
        method_bytes = method.encode("ascii")
    else:
        method_bytes = method

    if isinstance(path, str):
        path_bytes = path.encode("ascii")
    else:
        path_bytes = path

    prefix = b"/_matrix/identity/v2/"
    if shorthand:
        if not path_bytes.startswith(prefix):
            path_bytes = prefix.rstrip(b"/") + b"/" + path_bytes.lstrip(b"/")
    if not path_bytes.startswith(b"/"):
        path_bytes = b"/" + path_bytes

    if isinstance(content, dict):
        body_bytes = json.dumps(content).encode("utf-8")
    elif isinstance(content, text_type):
        body_bytes = content.encode("utf-8")
    else:
        body_bytes = content if isinstance(content, (bytes, bytearray)) else b""

    site = FakeSite(resource=None)
    channel = FakeChannel(reactor=reactor)
    req = request(channel, False, reactor)  # type: ignore[arg-type]

    req.content = BytesIO(body_bytes)
    req.requestHeaders = Headers()
    req.postpath = [unquote(p) for p in path_bytes.split(b"/") if p]

    if access_token is not None:
        req.requestHeaders.addRawHeader(b"Authorization", f"Bearer {access_token}".encode("utf-8"))
    if federation_auth_origin is not None:
        req.requestHeaders.addRawHeader(b"Authorization", f"X-Matrix origin={federation_auth_origin}".encode("utf-8"))
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")

    req.requestReceived(method_bytes, path_bytes, b"1.1")
    return req, channel