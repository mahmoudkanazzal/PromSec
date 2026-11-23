import os
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Callable

from twisted.internet import defer
from twisted.internet.defer import Deferred, succeed, fail
from twisted.internet.error import DNSLookupError
from twisted.internet.interfaces import (
    IReactorPluggableNameResolver,
    IResolverSimple,
    IHostnameResolver,
)
from twisted.test.proto_helpers import MemoryReactorClock
from twisted.logger import Logger
from twisted.web.http import Request
from twisted.web.server import Site
from twisted.web.http_headers import Headers
from twisted.names.resolve import SimpleResolverComplexifier

from sydent.sydent import Sydent

FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIID...
-----END CERTIFICATE-----"""

def make_sydent(test_config: Optional[Dict[str, Any]] = None) -> Sydent:
    """
    Create a Sydent instance for testing.

    Args:
        test_config: Optional dictionary to override default configuration.

    Returns:
        An initialized Sydent object using an in‑memory SQLite database and a
        ResolvingMemoryReactorClock.
    """
    config = {
        "database": {"type": "sqlite3", "connection": ":memory:"},
        "http": {"bind_address": "127.0.0.1", "port": 0},
        "sydent": {"server_name": "test"},
    }
    if test_config:
        config.update(test_config)
    reactor = ResolvingMemoryReactorClock()
    return Sydent(config, reactor=reactor)

@dataclass
class FakeChannel:
    """
    Minimal channel implementation used by Twisted Request objects in tests.
    """
    request: Request
    _body: bytes = b""

    @property
    def json_body(self) -> Any:
        try:
            return json.loads(self._body.decode("utf-8"))
        except Exception as e:
            raise ValueError("Invalid JSON body") from e

    def code(self) -> int:
        return self.request.code

    def headers(self) -> Headers:
        return self.request.responseHeaders

    def writeHeaders(self) -> None:
        self.request.writeHeaders(b"")

    def write(self, data: bytes) -> None:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("write() expects bytes")
        self._body += data
        self.request.write(data)

    def registerProducer(self, producer: Any, streaming: bool) -> None:
        self.request.registerProducer(producer, streaming)

    def unregisterProducer(self) -> None:
        self.request.unregisterProducer()

    def requestDone(self) -> None:
        if not self.request.finished:
            self.request.finish()

    def getPeer(self) -> Any:
        return self.request.getPeer()

    def getHost(self) -> Any:
        return self.request.getHost()

    @property
    def transport(self) -> Any:
        return self.request.transport

    def getPeerCertificate(self) -> Any:
        transport = getattr(self.request, "transport", None)
        if transport is None:
            raise AttributeError("Request has no transport")
        return getattr(transport, "getPeerCertificate", lambda: None)()

class FakeSite(Site):
    pass

def make_request(
    method: str,
    path: str,
    content: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    short: bool = False,
) -> FakeChannel:
    """
    Construct a fake HTTP request for testing.

    Args:
        method: HTTP method (e.g., "GET", "POST").
        path: Request path; if ``short`` is True, a default prefix is added.
        content: Optional request body; if a dict is provided it is JSON‑encoded.
        headers: Optional mapping of header names to values.
        short: If True, prepend "/_matrix/client/r0" to the path.

    Returns:
        A ``FakeChannel`` containing the prepared request.
    """
    if not isinstance(method, str):
        raise TypeError("method must be a string")
    if not isinstance(path, str):
        raise TypeError("path must be a string")
    if headers is not None and not isinstance(headers, dict):
        raise TypeError("headers must be a dict or None")
    if short:
        path = "/_matrix/client/r0" + (path if path.startswith("/") else "/" + path)
    body_bytes = b""
    request_headers = Headers()
    if content is not None:
        if isinstance(content, (dict, list)):
            body_bytes = json.dumps(content).encode("utf-8")
            request_headers.addRawHeader(b"content-type", b"application/json")
        elif isinstance(content, (bytes, bytearray)):
            body_bytes = bytes(content)
        elif isinstance(content, str):
            body_bytes = content.encode("utf-8")
        else:
            raise TypeError("Unsupported content type")
    if headers:
        for name, value in headers.items():
            if not isinstance(name, str) or not isinstance(value, str):
                raise TypeError("Header names and values must be strings")
            request_headers.addRawHeader(name.encode("utf-8"), value.encode("utf-8"))
    dummy_transport = None
    request = Request(
        channel=None,  # type: ignore[arg-type]
        queued=False,
    )
    request.method = method.encode("utf-8")
    request.uri = path.encode("utf-8")
    request.requestHeaders = request_headers
    request.content = defer.Deferred()
    request.content.callback(body_bytes)
    channel = FakeChannel(request=request)
    return channel

class ToTwistedHandler(logging.Handler):
    """
    Logging handler that forwards records to Twisted's logger named "sydent".
    """
    _level_map: Dict[int, Callable[[str], None]] = {
        logging.DEBUG: Logger(namespace="sydent").debug,
        logging.INFO: Logger(namespace="sydent").info,
        logging.WARNING: Logger(namespace="sydent").warn,
        logging.ERROR: Logger(namespace="sydent").error,
        logging.CRITICAL: Logger(namespace="sydent").critical,
    }

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            log_func = self._level_map.get(record.levelno, Logger(namespace="sydent").error)
            log_func(msg)
        except Exception:
            self.handleError(record)

def setup_logging() -> None:
    """
    Configure the root logger with ``ToTwistedHandler`` and environment‑driven level.
    """
    root_logger = logging.getLogger()
    handler = ToTwistedHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    root_logger.handlers = []
    root_logger.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR").upper()
    if not hasattr(logging, level_name):
        raise ValueError(f"Invalid log level: {level_name}")
    root_logger.setLevel(getattr(logging, level_name))

setup_logging()

class ResolvingMemoryReactorClock(MemoryReactorClock, IReactorPluggableNameResolver):
    """
    Memory reactor clock that also provides a simple name resolver.
    """
    def __init__(self) -> None:
        self.lookups: Dict[str, str] = {}

        class FakeResolver:
            implements = IResolverSimple

            def __init__(self, outer: "ResolvingMemoryReactorClock"):
                self._outer = outer

            def getHostByName(self, name: str, timeout: Optional[int] = None) -> Deferred:
                if name in self._outer.lookups:
                    return succeed(self._outer.lookups[name])
                return fail(DNSLookupError(f"Name {name} not found"))

        super().__init__()
        self.nameResolver = SimpleResolverComplexifier(FakeResolver(self))

    def installNameResolver(self, resolver: IHostnameResolver) -> IHostnameResolver:
        raise NotImplementedError()