import json
import os
import logging
from io import BytesIO
import attr
from six import text_type
from twisted.internet import address
from twisted.logger import Logger
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto
import sydent.sydent as sydent_mod

FAKE_SERVER_CERT_PEM = """
FAKE_CERT
"""

def make_sydent(test_config=None):
    if test_config is None:
        test_config = {}
    default_db = {"type": "sqlite3", "args": {"database": ":memory:"}}
    config_dict = {"database": default_db}
    config_dict.update(test_config)
    config = sydent_mod.parse_config_dict(config_dict)
    reactor = MemoryReactorClock()
    return sydent_mod.Sydent(reactor, config)

@attr.s
class FakeChannel:
    site = attr.ib()
    _reactor = attr.ib()
    result = attr.ib(factory=dict)
    _producer = attr.ib(default=None)

    @property
    def json_body(self):
        if not self.result:
            raise RuntimeError("No result available")
        body = self.result.get("body", b"")
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        return json.loads(body)

    @property
    def code(self):
        if not self.result:
            raise RuntimeError("No result available")
        return int(self.result.get("code", 0))

    @property
    def headers(self):
        if not self.result:
            raise RuntimeError("No result available")
        hdrs = self.result.get("headers", {})
        return Headers(hdrs)

    def writeHeaders(self, code, headers):
        self.result["code"] = code
        self.result["headers"] = dict(headers)

    def write(self, data):
        if "body" not in self.result:
            self.result["body"] = b""
        self.result["body"] += data

    def registerProducer(self, producer, streaming):
        if not getattr(self._reactor, "running", True):
            return
        self._producer = producer

    def unregisterProducer(self):
        self._producer = None

    def requestDone(self):
        pass

    def getPeer(self):
        return address.IPv4Address("TCP", "127.0.0.1", 12345)

    def getHost(self):
        return address.IPv4Address("TCP", "127.0.0.1", 80)

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
    if isinstance(method, text_type):
        method = method.encode("utf-8")
    if isinstance(path, text_type):
        path = path.encode("utf-8")
    if not isinstance(method, (bytes,)):
        raise TypeError("method must be bytes or text")
    if not isinstance(path, (bytes,)):
        raise TypeError("path must be bytes or text")
    try:
        method.decode("ascii")
        path.decode("ascii")
    except Exception:
        raise ValueError("method and path must be ASCII")
    if shorthand and not path.startswith(b"/_matrix"):
        path = b"/_matrix/identity/v2/" + path.lstrip(b"/")
    path = b"/" + path.lstrip(b"/")
    if isinstance(content, dict):
        body = json.dumps(content).encode("utf-8")
    elif isinstance(content, text_type):
        body = content.encode("utf-8")
    elif isinstance(content, bytes):
        body = content
    else:
        raise TypeError("content must be bytes, dict, or text")
    site = FakeSite()
    channel = FakeChannel(site=site, _reactor=reactor)
    req = request(channel)
    req.process = lambda: b""
    req.content = BytesIO(body)
    req.postpath = [unquote(p) for p in path.lstrip(b"/").split(b"/")]
    req.requestHeaders = Headers()
    if access_token is not None:
        token = access_token.encode("utf-8") if isinstance(access_token, text_type) else access_token
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + token)
    if federation_auth_origin is not None:
        origin = federation_auth_origin.encode("utf-8") if isinstance(federation_auth_origin, text_type) else federation_auth_origin
        req.requestHeaders.addRawHeader(b"Origin", origin)
    if body:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method, path, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.tx_log = Logger(self.__class__.__module__)

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            if level == "warning":
                level = "warn"
            log_method = getattr(self.tx_log, level, self.tx_log.error)
            log_method(msg)
        except Exception:
            self.handleError(record)

def setup_logging():
    root = logging.getLogger()
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    handler_present = any(isinstance(h, ToTwistedHandler) for h in root.handlers)
    if not handler_present:
        handler = ToTwistedHandler()
        handler.setFormatter(logging.Formatter(fmt))
        root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR").upper()
    level = getattr(logging, level_name, logging.ERROR)
    root.setLevel(level)

if not logging.getLogger().handlers:
    setup_logging()