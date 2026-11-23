import os
import json
import copy
import logging
import typing
import io
from dataclasses import dataclass, field

from OpenSSL import crypto
from twisted.internet.task import MemoryReactorClock
from twisted.internet.defer import succeed, fail, Deferred
from twisted.internet.error import DNSLookupError
from twisted.internet.interfaces import IReactorPluggableNameResolver
from twisted.web.server import Site, Request
from twisted.web.http_headers import Headers
from twisted.python import log as twisted_log
from sydent.sydent import Sydent


FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEbG9vZzANBgkqhkiG9w0BAQsFADBvMQswCQYDVQQGEwJV
UzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCk1vdW50YWluIFZpZXcxFjAUBgNVBAoT
DVNhbXBsZSBDb21wYW55MRUwEwYDVQQDEwxleGFtcGxlLmNvbTAeFw0yMTA1MDEw
MDAwMDBaFw0zMTA0MjkwMDAwMDBaMG8xCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJD
QTETMBEGA1UEBxMKTW91bnRhaW4gVmlldzEWMBQGA1UEChMNU2FtcGxlIENvbXBh
bnkxFTATBgNVBAMTDEXhbXBsZS5jb20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAw
ggEKAoIBAQC7V6V6w5K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6
V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6
V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6
V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6
V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6VwIDAQABo1AwTjAdBgNVHQ4EFgQUkK5v
Zc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5v
Zc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5v
Zc6V6K5vZc6V6K5vZc6V6K5vZc6V6K5vMA0GCSqGSIb3DQEBCwUAA4IBAQAB
-----END CERTIFICATE-----"""


class ResolvingMemoryReactorClock(MemoryReactorClock, IReactorPluggableNameResolver):
    """Memory reactor with a simple DNS resolver."""

    def __init__(self) -> None:
        super().__init__()
        self.lookups: dict[str, str] = {}
        self.resolver = self.FakeResolver(self.lookups)

    def installNameResolver(self, resolver) -> None:  # type: ignore[override]
        raise NotImplementedError("installNameResolver is not supported")

    class FakeResolver:
        def __init__(self, lookups: dict[str, str]) -> None:
            self.lookups = lookups

        def getHostByName(self, name: str, timeout: typing.Optional[int] = None) -> Deferred:
            if name in self.lookups:
                return succeed(self.lookups[name])
            return fail(DNSLookupError(name))


def make_sydent(test_config: typing.Optional[dict] = None) -> Sydent:
    """Create a Sydent instance with optional test configuration."""
    if test_config is not None and not isinstance(test_config, dict):
        raise TypeError("test_config must be a dict or None")
    config = copy.deepcopy(test_config) if test_config else {}
    config.setdefault("use_tls_for_federation", False)
    reactor = ResolvingMemoryReactorClock()
    return Sydent(reactor=reactor, config=config)


def _create_fake_channel(site: Site, reactor: ResolvingMemoryReactorClock) -> "FakeChannel":
    """Create a FakeChannel with a deep‑copied Site."""
    if not isinstance(site, Site):
        raise TypeError("site must be a twisted.web.server.Site instance")
    if not isinstance(reactor, ResolvingMemoryReactorClock):
        raise TypeError("reactor must be a ResolvingMemoryReactorClock instance")
    site_copy = copy.deepcopy(site)
    return FakeChannel(site=site_copy, _reactor=reactor, result={}, _producer=None)


class FakeSite(Site):
    """Site subclass with no default resource."""

    def __init__(self) -> None:
        super().__init__(resource=None)


@dataclass
class FakeChannel:
    site: Site
    _reactor: ResolvingMemoryReactorClock
    result: dict = field(default_factory=dict)
    _producer: typing.Any = None

    @property
    def json_body(self) -> typing.Any:
        """Decode JSON body from result."""
        if "body" not in self.result:
            raise KeyError("result missing 'body'")
        body = self.result["body"]
        if not isinstance(body, (bytes, bytearray)):
            raise TypeError("'body' must be bytes")
        try:
            text = body.decode("utf-8")
        except Exception as e:
            raise TypeError("body decoding failed") from e
        return json.loads(text)

    @property
    def code(self) -> int:
        """Return HTTP status code."""
        if "code" not in self.result:
            raise KeyError("result missing 'code'")
        code = self.result["code"]
        if not isinstance(code, int):
            raise TypeError("'code' must be int")
        return code

    @property
    def headers(self) -> Headers:
        """Convert raw headers dict to Headers object."""
        raw = self.result.get("headers", {})
        if not isinstance(raw, dict):
            raise TypeError("'headers' must be a dict")
        hdrs = Headers()
        for k, v in raw.items():
            if not isinstance(k, (bytes, bytearray)):
                raise TypeError("header keys must be bytes")
            if not isinstance(v, (bytes, bytearray)):
                raise TypeError("header values must be bytes")
            hdrs.addRawHeader(k.decode("utf-8"), v.decode("utf-8"))
        return hdrs

    def writeHeaders(self, headers: dict[bytes, bytes]) -> None:
        """Store response headers."""
        if not isinstance(headers, dict):
            raise TypeError("headers must be a dict")
        for k, v in headers.items():
            if not isinstance(k, (bytes, bytearray)):
                raise TypeError("header keys must be bytes")
            if not isinstance(v, (bytes, bytearray)):
                raise TypeError("header values must be bytes")
        self.result["headers"] = {k: v for k, v in headers.items()}

    def write(self, data: bytes) -> None:
        """Append data to response body."""
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")
        existing = self.result.get("body", b"")
        if not isinstance(existing, (bytes, bytearray)):
            raise TypeError("existing body must be bytes")
        self.result["body"] = existing + data

    def registerProducer(self, producer: typing.Any, streaming: bool) -> None:
        """Register a producer."""
        self._producer = producer

    def unregisterProducer(self) -> None:
        """Unregister the producer."""
        self._producer = None

    def requestDone(self) -> None:
        """Mark request as done."""
        self.result.setdefault("done", True)

    def getPeer(self) -> typing.Any:
        """Return a fake peer address."""
        return type("Peer", (), {"host": "127.0.0.1", "port": 0})()

    def getHost(self) -> typing.Any:
        """Return a fake host address."""
        return type("Host", (), {"host": "127.0.0.1", "port": 0})()

    @property
    def transport(self) -> typing.Any:
        """Return a transport with a fake certificate."""
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM)

        class Transport:
            def getPeerCertificate(self) -> crypto.X509:
                return cert

        return Transport()

    def getPeerCertificate(self) -> crypto.X509:
        """Return the fake X509 certificate."""
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM)


def make_request(
    reactor: ResolvingMemoryReactorClock,
    site: Site,
    method: typing.Union[str, bytes],
    path: typing.Union[str, bytes],
    content: typing.Optional[typing.Union[dict, str, bytes, bytearray]] = None,
    shorthand: bool = False,
    auth: typing.Optional[str] = None,
    origin: typing.Optional[str] = None,
) -> tuple[Request, FakeChannel]:
    """Build a synthetic Request and associated FakeChannel."""
    if not isinstance(reactor, ResolvingMemoryReactorClock):
        raise TypeError("reactor must be a ResolvingMemoryReactorClock")
    if not isinstance(site, Site):
        raise TypeError("site must be a Site")
    if isinstance(method, str):
        method_bytes = method.encode("utf-8")
    elif isinstance(method, (bytes, bytearray)):
        method_bytes = bytes(method)
    else:
        raise TypeError("method must be str or bytes")
    if isinstance(path, str):
        path_bytes = path.encode("utf-8")
    elif isinstance(path, (bytes, bytearray)):
        path_bytes = bytes(path)
    else:
        raise TypeError("path must be str or bytes")
    if shorthand:
        path_bytes = b"/_matrix" + (path_bytes if path_bytes.startswith(b"/") else b"/" + path_bytes)
    if isinstance(content, dict):
        body_bytes = json.dumps(content).encode("utf-8")
        content_type = b"application/json"
    elif isinstance(content, str):
        body_bytes = content.encode("utf-8")
        content_type = b"text/plain"
    elif isinstance(content, (bytes, bytearray)):
        body_bytes = bytes(content)
        content_type = b"application/octet-stream"
    else:
        body_bytes = b""
        content_type = None
    channel = _create_fake_channel(site, reactor)
    request = Request(channel, False)
    request.method = method_bytes
    request.uri = path_bytes
    request.path = path_bytes
    request.content = io.BytesIO(body_bytes)
    request.requestHeaders = Headers()
    if auth is not None:
        request.requestHeaders.addRawHeader(b"Authorization", auth.encode("utf-8"))
    if origin is not None:
        request.requestHeaders.addRawHeader(b"Origin", origin.encode("utf-8"))
    if content_type is not None:
        request.requestHeaders.addRawHeader(b"Content-Type", content_type)
    decoded_path = path_bytes.split(b"?", 1)[0]
    request.postpath = [segment for segment in decoded_path.split(b"/") if segment]
    request.requestReceived(method_bytes, path_bytes, b"HTTP/1.1")
    return request, channel


class ToTwistedHandler(logging.Handler):
    """Logging handler forwarding records to Twisted logger."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if record.levelno >= logging.ERROR:
                twisted_log.err(msg)
            elif record.levelno >= logging.WARNING:
                twisted_log.msg(msg, logLevel=logging.WARNING)
            elif record.levelno >= logging.INFO:
                twisted_log.msg(msg, logLevel=logging.INFO)
            else:
                twisted_log.msg(msg, logLevel=logging.DEBUG)
        except Exception:
            self.handleError(record)


def setup_logging() -> None:
    """Configure module logger to forward to Twisted."""
    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.handlers.clear()
    handler = ToTwistedHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR").upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        level = logging.ERROR
    logger.setLevel(level)


if os.getenv("SYDENT_AUTO_SETUP_LOGGING", "1").lower() not in ("0", "false"):
    setup_logging()