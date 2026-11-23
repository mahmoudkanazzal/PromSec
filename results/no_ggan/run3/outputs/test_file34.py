import os
import json
import logging
from io import BytesIO
from typing import Any, Dict, List, Tuple, Union, Optional
import attr
from urllib.parse import unquote_to_bytes
from OpenSSL import crypto
from twisted.logger import Logger as TwistedLogger
from twisted.web.http_headers import Headers
from twisted.web.server import Request
from twisted.test.proto_helpers import MemoryReactorClock


FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEbG9vZzANBgkqhkiG9w0BAQsFADBvMQswCQYDVQQGEwJV
UzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCk1vdW50YWluIFZpZXcxFjAUBgNVBAoT
DVN5ZGVudCBJbmMuMRUwEwYDVQQDEwxteS5leGFtcGxlLmNvbTAeFw0yMTA1MDEx
MjAwMDBaFw0zMTA0MjkxMjAwMDBaMG8xCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJD
QTETMBEGA1UEBxMKTW91bnRhaW4gVmlldzEWMBQGA1UEChMNU3lkZW50IEluYy4x
FTATBgNVBAMTDG15LmV4YW1wbGUuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A
MIIBCgKCAQEAxV6V6wX6Z1GDZCBoBPXaG9q4CPGK/c/pX9nuS3GgEcg2YkdE+5E9
k6l2b7xvFeoJEB6Digw1k3D6Z0SqnX+0Gooy2cwr6jciJ6TP2PzefRg2fzGEGZm4
6dkprdFM5lTyBC0bYKT1eZq9VHtV6nRvWmvMRGsiE9z1FMvx6bMpiKFFitvolG/G
hgbf+5Q5e0M1Y9hw3rroWAtxEvsC0BpvyEukgqS0bkkCm1cW0XOxKxO6jwxKF1u9
MaivGi99ZTSdK6Ff8gDuwZQzQ0jrISFRCGDpa2BkLomqKgJo0vvVuv5AO9M/dwZ0
gS3pS3kMt2rt7NmBGG99nmCaTKty+O+kOQIDAQABo1AwTjAdBgNVHQ4EFgQUx2dr
r/7EQo1gChX2NDVY5QZnQgwwHwYDVR0jBBgwFoAUx2drr/7EQo1gChX2NDVY5QZn
QgwwDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAt5lHppZArYdS9x+h
cYfZcQ3VIAtF5NCz7L+G5kZZgwyU0YJIUKGwEuITdSb9VjA36TObgGJE0E7E5Wdl
iRS0LlwM1c01qmPvvrLpzjAU6YewsGQKzBSSMSmc5QwDFi1Cdm42Hcps225y7sY/
qsK0kGugHgd6NqBJ38qRAjPR9U1FVLtZL1NVr7Di5urN6byN1Nsx3Rp3XIan+FQI
uxMxDPZWS9Vyuk3F7S3w7Dnk3a1JpN96CB2A+qsYqSdz+CA0nVddOZXS6jttuPAo
+K6TfGsDz3jAC5vVsQt1zArhcXd1LSeXfhBF3/f6/Dr7guP5AnbcW2CYwiVdc+Gq
Gw==
-----END CERTIFICATE-----"""


def _validate_ascii_token(token: str) -> bytes:
    if not isinstance(token, str):
        raise TypeError("Token must be a string")
    if any(ord(c) < 33 or ord(c) > 126 or c.isspace() for c in token):
        raise ValueError("Token contains invalid characters")
    token_bytes = token.encode("ascii")
    _validate_header_value(token_bytes)
    return token_bytes


def _validate_header_value(value: bytes) -> None:
    if not isinstance(value, (bytes, bytearray)):
        raise TypeError("Header value must be bytes")
    if b"\r" in value or b"\n" in value:
        raise ValueError("Header value must not contain CR or LF")
    if any(b < 32 or b > 126 for b in value):
        raise ValueError("Header value contains non‑printable ASCII characters")


def _validate_http_method(method: Union[str, bytes]) -> bytes:
    if isinstance(method, bytes):
        try:
            method_str = method.decode("ascii")
        except Exception as e:
            raise ValueError("HTTP method bytes must be ASCII") from e
    elif isinstance(method, str):
        method_str = method
    else:
        raise TypeError("HTTP method must be str or bytes")
    method_upper = method_str.upper()
    token_bytes = _validate_ascii_token(method_upper)
    allowed = {b"GET", b"POST", b"PUT", b"DELETE", b"PATCH", b"HEAD", b"OPTIONS"}
    if token_bytes not in allowed:
        raise ValueError(f"HTTP method {method_upper!r} is not allowed")
    return token_bytes


def _validate_path_bytes(path_bytes: bytes) -> bytes:
    if not isinstance(path_bytes, (bytes, bytearray)):
        raise TypeError("Path must be bytes")
    _validate_header_value(path_bytes)
    return path_bytes


@attr.s(auto_attribs=True, slots=True)
class FakeChannel:
    body: bytearray = attr.ib(factory=bytearray)
    _headers: Dict[bytes, List[bytes]] = attr.ib(factory=dict, init=False)
    _code: Optional[int] = attr.ib(default=None, init=False)
    _result_body: bytes = attr.ib(default=b"", init=False)

    @property
    def json_body(self):
        if not self._result_body:
            raise RuntimeError("Result is empty")
        return json.loads(self._result_body.decode("utf-8"))

    @property
    def code(self):
        if not self._result_body:
            raise RuntimeError("Result is empty")
        return self._code

    @property
    def headers(self):
        if not self._result_body:
            raise RuntimeError("Result is empty")
        return self._headers

    def writeHeaders(self, code: int, headers: List[Tuple[bytes, bytes]]) -> None:
        if not isinstance(code, int):
            raise TypeError("Status code must be int")
        self._code = code
        for name, value in headers:
            if isinstance(name, bytes):
                name_str = name.decode("ascii")
            elif isinstance(name, str):
                name_str = name
            else:
                raise TypeError("Header name must be str or bytes")
            name_bytes = _validate_ascii_token(name_str)
            if not isinstance(value, (bytes, bytearray)):
                raise TypeError("Header value must be bytes")
            value_bytes = bytes(value)
            _validate_header_value(value_bytes)
            self._headers.setdefault(name_bytes, []).append(value_bytes)

    def write(self, data: Union[bytes, bytearray, memoryview]) -> None:
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("Data must be bytes‑like")
        self.body.extend(data)

    def registerProducer(self, producer, streaming):
        self._producer = producer
        self._streaming = streaming

    def unregisterProducer(self):
        self._producer = None

    def requestDone(self):
        self._result_body = bytes(self.body)

    def getPeer(self):
        return type("Peer", (), {"host": "127.0.0.1", "port": 0})()

    def getHost(self):
        return type("Host", (), {"host": "127.0.0.1", "port": 0})()

    @property
    def transport(self):
        return self

    def getPeerCertificate(self):
        try:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM.encode("utf-8"))
            return cert
        except Exception as e:
            raise RuntimeError("Failed to load peer certificate") from e


class FakeSite:
    pass


def make_sydent(test_config: Union[Dict[str, Any], None] = None):
    base_config = {
        "database": {"type": "sqlite3", "database": ":memory:"},
        "reactor": MemoryReactorClock(),
    }
    if test_config:
        base_config.update(test_config)
    return Sydent(base_config)


def make_request(
    request: type,
    method: Union[str, bytes],
    path: Union[str, bytes],
    content: Union[Dict[str, Any], str, bytes, None] = None,
    access_token: Union[str, None] = None,
    federation_auth_origin: Union[str, bytes, None] = None,
    shorthand: bool = True,
) -> Tuple[Request, FakeChannel]:
    method_bytes = _validate_http_method(method)

    if isinstance(path, str):
        path_bytes = path.encode("utf-8")
    else:
        path_bytes = path
    path_bytes = _validate_path_bytes(path_bytes)

    if shorthand and not path_bytes.startswith(b"/_matrix"):
        path_bytes = b"/_matrix/identity/v2/" + path_bytes.lstrip(b"/")
        while b"//" in path_bytes:
            path_bytes = path_bytes.replace(b"//", b"/")

    if content is None:
        body_bytes = b""
    elif isinstance(content, dict):
        body_bytes = json.dumps(content).encode("utf-8")
    elif isinstance(content, str):
        body_bytes = content.encode("utf-8")
    elif isinstance(content, (bytes, bytearray, memoryview)):
        body_bytes = bytes(content)
    else:
        raise TypeError("Unsupported content type")

    site = FakeSite()
    channel = FakeChannel()
    req = request(channel)  # type: ignore
    req.process = lambda: b""
    req.content = BytesIO(body_bytes)

    segments = [seg for seg in path_bytes.split(b"/") if seg]
    unquoted = []
    for seg in segments:
        decoded = unquote_to_bytes(seg)
        if decoded == b"..":
            raise ValueError("Path segment '..' is not allowed")
        unquoted.append(decoded)
    req.postpath = unquoted

    req.requestHeaders = Headers()

    if access_token is not None:
        token_bytes = _validate_ascii_token(access_token)
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + token_bytes)

    if federation_auth_origin is not None:
        if isinstance(federation_auth_origin, bytes):
            origin_str = federation_auth_origin.decode("utf-8")
        else:
            origin_str = federation_auth_origin
        origin_bytes = _validate_ascii_token(origin_str)
        header_value = b"X-Matrix origin=" + origin_bytes + b",key=,sig="
        req.requestHeaders.addRawHeader(b"Authorization", header_value)

    if body_bytes:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")

    req.requestReceived(method_bytes, path_bytes, b"1.1")
    return req, channel


class ToTwistedHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._twisted_logger = TwistedLogger()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            level_name = record.levelname.lower()
            if level_name == "warning":
                level_name = "warn"
            log_method = getattr(self._twisted_logger, level_name, self._twisted_logger.error)
            log_method(msg)
        except Exception:
            self.handleError(record)


def setup_logging() -> None:
    root = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s")
    if not any(isinstance(h, ToTwistedHandler) for h in root.handlers):
        handler = ToTwistedHandler()
        handler.setFormatter(formatter)
        root.addHandler(handler)
    level_str = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR").upper()
    level = getattr(logging, level_str, None)
    if not isinstance(level, int):
        level = logging.ERROR
    root.setLevel(level)


setup_logging()