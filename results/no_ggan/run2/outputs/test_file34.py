import os
import json
import logging
from io import BytesIO
from typing import Tuple, Any, Dict, Optional

import attr
from six import text_type
from twisted.internet.address import IPv4Address
from twisted.logger import Logger as TwistedLogger
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto

def _generate_fake_cert() -> str:
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 1024)
    cert = crypto.X509()
    cert.get_subject().CN = "Fake Cert"
    cert.set_serial_number(1)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, "sha256")
    return crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode()

FAKE_SERVER_CERT_PEM = _generate_fake_cert()

def make_sydent(test_config: Optional[Dict[str, Any]] = None):
    from sydent.sydent import Sydent, parse_config_dict
    cfg = dict(test_config or {})
    cfg.setdefault("db.file", ":memory:")
    reactor = MemoryReactorClock()
    return Sydent(reactor, parse_config_dict(cfg))

def _sanitize_header_value(value: bytes) -> bytes:
    return value.replace(b'\r', b'').replace(b'\n', b'')

@attr.s(auto_attribs=True, slots=True)
class FakeChannel:
    site: Any
    _reactor: Any
    result: Dict[str, Any] = attr.Factory(dict)
    _producer: Any = None

    @property
    def json_body(self):
        if not self.result:
            raise RuntimeError("No result")
        return json.loads(self.result["body"])

    @property
    def code(self):
        if not self.result:
            raise RuntimeError("No result")
        return self.result["code"]

    @property
    def headers(self):
        if not self.result:
            raise RuntimeError("No result")
        return Headers(self.result["headers"])

    def writeHeaders(self, headers):
        self.result["headers"] = {k: v for k, v in headers.getAllRawHeaders()}

    def write(self, data):
        body = self.result.get("body", b"")
        if isinstance(body, str):
            body = body.encode()
        self.result["body"] = body + data

    def registerProducer(self, producer, streaming):
        self._producer = producer

    def unregisterProducer(self):
        self._producer = None

    def requestDone(self, _):
        pass

    def getPeer(self):
        return IPv4Address("TCP", "127.0.0.1", 12345)

    def getHost(self):
        return IPv4Address("TCP", "127.0.0.1", 80)

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
    content: Any = b"",
    access_token: Optional[text_type] = None,
    request: Any = Request,
    shorthand: bool = True,
    federation_auth_origin: Optional[text_type] = None,
) -> Tuple[Request, FakeChannel]:
    if isinstance(method, text_type):
        method_bytes = method.encode("ascii")
    else:
        method_bytes = method
    if isinstance(path, text_type):
        path_str = path
    else:
        path_str = path.decode("utf-8")
    if shorthand and not path_str.startswith("/_matrix"):
        path_str = "/_matrix/identity/v2/" + path_str.lstrip("/")
    if not path_str.startswith("/"):
        path_str = "/" + path_str
    path_bytes = path_str.encode("utf-8")
    if isinstance(content, dict):
        body_bytes = json.dumps(content).encode("utf-8")
    elif isinstance(content, text_type):
        body_bytes = content.encode("utf-8")
    else:
        body_bytes = content
    site = FakeSite()
    channel = FakeChannel(site, reactor)
    req = request(channel, False, reactor)
    req.requestHeaders = Headers()
    req.content = BytesIO(body_bytes)
    req.postpath = []
    if access_token is not None:
        token_bytes = _sanitize_header_value(access_token.encode("utf-8"))
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + token_bytes)
    if federation_auth_origin is not None:
        origin_bytes = _sanitize_header_value(federation_auth_origin.encode("utf-8"))
        auth_value = b"X-Matrix origin=" + origin_bytes + b",key=,sig="
        req.requestHeaders.addRawHeader(b"Authorization", auth_value)
    if body_bytes:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method_bytes, path_bytes, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.tx_log = TwistedLogger()

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelno
            if level >= logging.CRITICAL:
                method = self.tx_log.critical
            elif level >= logging.ERROR:
                method = self.tx_log.error
            elif level >= logging.WARNING:
                method = self.tx_log.warn
            elif level >= logging.INFO:
                method = self.tx_log.info
            else:
                method = self.tx_log.debug
            method(msg)
        except Exception:
            self.handleError(record)

def setup_logging():
    root = logging.getLogger()
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    if not any(isinstance(h, ToTwistedHandler) for h in root.handlers):
        handler = ToTwistedHandler()
        handler.setFormatter(logging.Formatter(fmt))
        root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR")
    root.setLevel(getattr(logging, level_name.upper(), logging.ERROR))

setup_logging()