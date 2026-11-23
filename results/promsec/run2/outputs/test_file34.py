import json
from io import BytesIO
import logging
import os
import attr
from six import text_type
from twisted.internet import address
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto
from sydent.sydent import Sydent, parse_config_dict
from twisted.logger import Logger, LogLevel

FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEbG9vZDAKBggqhkjOPQQDAjCBkzELMAkGA1UEBhMCVVMx
CzAJBgNVBAgMAkNBMRAwDgYDVQQHDAdTYW4gSm9zZTEVMBMGA1UECgwMTXkgQ29t
cGFueSBJbmMxFjAUBgNVBAsMDVRlY2ggRGVwYXJ0bWVudDEYMBYGA1UEAwwPd3d3
LmV4YW1wbGUuY29tMB4XDTIxMDkwMTAwMDAwMFoXDTMxMDgyOTIzNTk1OVowgZMx
CzAJBgNVBAYTAlVTMQswCQYDVQQIDAJDQTEQMA4GA1UEBwwHU2FuIEpvc2UxFTAT
BgNVBAoMDE15IENvbXBhbnkgSW5jMRYwFAYDVQQLDA1UZWNoIERlcGFydG1lbnQx
GDAWBgNVBAMMD3d3dy5leGFtcGxlLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEP
ADCCAQoCggEBAL6V6wX6Z1GDZCBoBPuiGNsq4CPGK/c/pX9nuSUXwxLBzME2YkdB
5EYXPLkZXl2b7xvFeoJEB6Digw1VE3D6Z0SqnX+0Gooy2cwr6jciJ6TP2PzefRg2
oGZm4G6dkprdFM5lTyBC0bYKT1eZq9VHtV6nRvWmvMRGsiE9z1FMvx6bMpiKFFit
GZrxhgbf+5Q5e0M1Y9hw3rroWAtxEvsC0BpvyEukgqS0bkkCm1cW0XkyRjO6jwxm
u9IiMaivGi99ZTSdK6Ff8gDuwZQzQ0jrISFRCGDpa2BkLomqKgJo0vvVuv5AO9M1
Z0pniS3pSke1Mt2rt7NmBGG99nmCaTKty+0CAwEAAaNTMFEwHQYDVR0OBBYEFAsl
x2drXr/7EQo1gChX2NDVY5QvMB8GA1UdIwQYMBaAFAslx2drXr/7EQo1gChX2NDV
Y5QvMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBABZArYdS9x+h
cYfZcQ3VIAtF5NCz7L+G5kZZgwyU0YJIUKGwEuITdSb9VjA36TObgGJE0E7E5Wdl
T4kLlwM1c01qmPvvrLpzjAU6YewsGQKzBSSMSmc5QwDFi1Cdm42Hcps225y7sY9V
0kGugHgd6NqBJ38qJNmPR9U1FVLtZL1NVr7Di5urN6byN1Nsx3Rp3XIan+FJxux1
ZWS9Vyuk3F7S3w7Dnk3a1JpN96CB2A+qsYqSdz+CA0nVddOZXS6jttuPAHyBs+K6
nDz3jAC5vVsQt1zArhcXd1LSeXfhBF3/f6/Dr7guP5AnbcW2CYwiVdc+GqORdz8=
-----END CERTIFICATE-----"""

def make_sydent(test_config=None):
    if test_config is None:
        test_config = {}
    test_config.setdefault("db", {})
    test_config["db"].setdefault("db.file", ":memory:")
    reactor = MemoryReactorClock()
    return Sydent(reactor=reactor, cfg=parse_config_dict(test_config))

@attr.s(auto_attribs=True, slots=True)
class FakeChannel:
    site: Site
    _reactor: object
    result: dict = attr.Factory(dict)
    _producer = None

    @property
    def json_body(self):
        if not self.result:
            raise Exception("No result yet.")
        return json.loads(self.result["body"].decode("utf8"))

    @property
    def code(self):
        if not self.result:
            raise Exception("No result yet.")
        return int(self.result["code"])

    @property
    def headers(self):
        if not self.result:
            raise Exception("No result yet.")
        hdrs = Headers()
        for name, value in self.result.get("headers", []):
            hdrs.addRawHeader(name, value)
        return hdrs

    def writeHeaders(self, version, code, reason, headers):
        self.result["version"] = version
        self.result["code"] = code
        self.result["reason"] = reason
        self.result["headers"] = list(headers)
        self.result.setdefault("body", b"")

    def write(self, content):
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError("content must be bytes")
        self.result["body"] = self.result.get("body", b"") + content

    def registerProducer(self, producer, streaming):
        self._producer = producer
        if not streaming:
            def resume():
                if self._producer is not None:
                    self._producer.resumeProducing()
                    self._reactor.callLater(0.1, resume)
            self._reactor.callLater(0.1, resume)

    def unregisterProducer(self):
        self._producer = None

    def requestDone(self, _self):
        self.result["done"] = True

    def getPeer(self):
        return address.IPv4Address("TCP", "127.0.0.1", 3423)

    def getHost(self):
        return None

    @property
    def transport(self):
        return self

    def getPeerCertificate(self):
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM)

class FakeSite:
    pass

def make_request(reactor, method, path, content=b"", access_token=None, request=Request, shorthand=True, federation_auth_origin=None):
    if not isinstance(method, bytes):
        method = method.encode("utf8")
    if not isinstance(path, bytes):
        path = path.encode("utf8")
    if shorthand and not path.startswith(b"/_matrix"):
        path = b"/_matrix/identity/v2/" + path.lstrip(b"/")
        while b"//" in path:
            path = path.replace(b"//", b"/")
    if not path.startswith(b"/"):
        path = b"/" + path
    if isinstance(content, dict):
        content = json.dumps(content).encode("utf8")
    elif isinstance(content, text_type):
        content = content.encode("utf8")
    site = FakeSite()
    channel = FakeChannel(site, reactor)
    req = request(channel)
    req.process = lambda: b""
    req.content = BytesIO(content)
    decoded_path = unquote(path)
    req.postpath = [segment for segment in decoded_path.split(b"/") if segment]
    if access_token is not None:
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + access_token.encode("utf8") if isinstance(access_token, str) else b"Bearer " + access_token)
    if federation_auth_origin is not None:
        header = b"X-Matrix origin=%b,key=,sig=" % federation_auth_origin.encode("utf8") if isinstance(federation_auth_origin, str) else b"X-Matrix origin=%b,key=,sig=" % federation_auth_origin
        req.requestHeaders.addRawHeader(b"Authorization", header)
    if content:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method, path, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.tx_log = Logger()

    def emit(self, record):
        log_entry = self.format(record)
        level_name = record.levelname.lower()
        if level_name == "warning":
            level_name = "warn"
        level = LogLevel.levelWithName(level_name)
        self.tx_log.emit(level, "{entry}", entry=log_entry)

def setup_logging():
    root = logging.getLogger()
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    handler = ToTwistedHandler()
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR")
    root.setLevel(getattr(logging, level_name.upper(), logging.ERROR))