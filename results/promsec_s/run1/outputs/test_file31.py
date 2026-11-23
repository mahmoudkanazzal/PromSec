import json
from io import BytesIO
import logging
import os
from typing import Dict
from dataclasses import dataclass, field
from six import text_type
from zope.interface import implementer
from twisted.internet._resolver import SimpleResolverComplexifier
from twisted.internet.defer import fail, succeed
from twisted.internet.error import DNSLookupError
from twisted.internet.interfaces import IHostnameResolver, IReactorPluggableNameResolver, IResolverSimple
from twisted.internet import address
import twisted.logger
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto
from sydent.sydent import Sydent, parse_config_dict

FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEbG9vZzANBgkqhkiG9w0BAQsFADBvMQswCQYDVQQGEwJV
UzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCk1vdW50YWluIFZpZXcxFjAUBgNVBAoT
DVN5ZGVudCBJbmMuMRUwEwYDVQQDEwxUZXN0IENlcnRpZmljYXRlMB4XDTIxMDkw
MTAwMDAwMFoXDTMxMDgyOTIzNTk1OVowbzELMAkGA1UEBhMCVVMxCzAJBgNVBAgT
AkNBMRMwEQYDVQQHEwpNb3VudGFpbiBWaWV3MRYwFAYDVQQKEw1TeWRlbnQgSW5j
LjEVMBMGA1UEAxMMVGVzdCBDZXJ0aWZpY2F0ZTCCASIwDQYJKoZIhvcNAQEBBQAD
ggEPADCCAQoCggEBAL6V6wX6Z1GDZCBoBPXaGNsq4CPGK/c/pX9nuSUXwxLBzMEG
iE+5EYXPLkZXl2b7xvFeoJEB6Digw1VE3D6Z0SqnX+0Gooy2cwr6jciJ6TP2Pzef
oAJGEGZm4G6dkprdFM5lTyBC0bYKT1eZq9VHtV6nRvWmvMRGsiE9z1FMvx6bMpiK
nzvolG/GpNZgbf+5Q5e0M1Vo9hw3rroWAt4EvsC0BpvyEukgqS0bkkCm1cW0XkyR
O6jwxKF1u9IiMaivGi99ZTSdK6Ff8gDuwZQzQ0jrISFRCGDpa2BkLomqKgJo0vvV
5AO9M/dwZ0pniS3pSke1Mt2rt7NmBGG99nmCaXMCAwEAAaNQME4wHQYDVR0OBBYE
FKKBslZx2drXr/7EQo1gChX2NDVYMB8GA1UdIwQYMBaAFKKBslZx2drXr/7EQo1g
ChX2NDVYMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAJfq5lHppZAr
rS9x+h0cYfZcQ3VIAtF5NCz7L+G5kZZgwyU0YJIUKGwEuKXXSb9VjA36TObgGJE0
arE5Wdl0iRS0LlwM1c01qmPvvrLpzjAU6YewsGQKzBSSMSmc5QwDFi1Cdm42Hcps
y7sY9qsK0kGugHgd6NqBJ38qRAjPR9U1FVLtZL1NVr7Di5urN6byN1Nsx3Rp3XIan
nKxuxMxDPZWS9Vyuk3F7S3w7Dnk3a1JpN96CB2A+qsYqSdz+CA0nVddOZXS6jttu
HyBs+K6TfGsDz3jAC5vVsQt1zArhcXd1LSeXfhBF3/f6/Dr7guP5AnbcWcCYwiVQ
pVORdz8=
-----END CERTIFICATE-----"""

def make_sydent(test_config={}):
    if "db" not in test_config:
        test_config["db"] = {}
    if "db.file" not in test_config["db"]:
        test_config["db"]["db.file"] = ":memory:"
    reactor = ResolvingMemoryReactorClock()
    return Sydent(reactor=reactor, cfg=parse_config_dict(test_config), use_tls_for_federation=False)

@dataclass
class FakeChannel:
    site: Site
    _reactor: any
    result: dict = field(default_factory=dict)
    _producer: any = None

    @property
    def json_body(self):
        if not self.result:
            raise Exception("Result is empty")
        return json.loads(self.result.get("body", b"").decode("utf-8"))

    @property
    def code(self):
        if not self.result:
            raise Exception("Result is empty")
        return self.result.get("code")

    @property
    def headers(self):
        if not self.result:
            raise Exception("Result is empty")
        return Headers(self.result.get("headers", []))

    def writeHeaders(self, version, code, reason, headers):
        self.result["code"] = code
        self.result["reason"] = reason
        self.result["headers"] = headers
        self.result["body"] = b""

    def write(self, content):
        if not isinstance(content, bytes):
            raise TypeError("Content must be bytes")
        self.result["body"] = self.result.get("body", b"") + content

    def registerProducer(self, producer, streaming):
        self._producer = producer
        if not streaming:
            producer.resumeProducing()
        else:
            def resume():
                if self._producer:
                    self._producer.resumeProducing()
                    self._reactor.callLater(0, resume)
            self._reactor.callLater(0, resume)

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
    if not isinstance(method, bytes):
        method = method.encode("utf-8") if isinstance(method, text_type) else bytes(method)
    if not isinstance(path, bytes):
        path = path.encode("utf-8") if isinstance(path, text_type) else bytes(path)
    if shorthand and not path.startswith(b"/_matrix"):
        path = b"/_matrix/identity/v2/" + path.lstrip(b"/")
        while b"//" in path:
            path = path.replace(b"//", b"/")
    if not path.startswith(b"/"):
        path = b"/" + path
    if isinstance(content, dict):
        content_bytes = json.dumps(content).encode("utf-8")
    elif isinstance(content, text_type):
        content_bytes = content.encode("utf-8")
    else:
        content_bytes = content
    site = FakeSite()
    channel = FakeChannel(site, reactor)
    req = request(channel)
    req.process = lambda: b""
    req.content = BytesIO(content_bytes)
    req.requestHeaders = Headers()
    req.postpath = [unquote(p) for p in path.split(b"/") if p]
    if access_token is not None:
        token = access_token.encode("utf-8") if isinstance(access_token, text_type) else access_token
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + token)
    if federation_auth_origin is not None:
        origin = federation_auth_origin.encode("utf-8") if isinstance(federation_auth_origin, text_type) else federation_auth_origin
        header = b"X-Matrix origin=%s,key=,sig=" % origin
        req.requestHeaders.addRawHeader(b"Authorization", header)
    if content_bytes:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method, path, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    tx_log = twisted.logger.Logger(namespace="sydent")
    def emit(self, record):
        msg = self.format(record)
        level = record.levelname.lower()
        if level == "warning":
            level = "warn"
        lvl = twisted.logger.LogLevel.levelWithName(level)
        self.tx_log.emit(lvl, msg)

def setup_logging():
    root = logging.getLogger()
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    handler = ToTwistedHandler()
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)
    root.setLevel(os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR"))

setup_logging()

@implementer(IReactorPluggableNameResolver)
class ResolvingMemoryReactorClock(MemoryReactorClock):
    def __init__(self):
        self.lookups: Dict[str, str] = {}
        class FakeResolver:
            def getHostByName(inner_self, name, timeout=None):
                if name not in self.lookups:
                    return fail(DNSLookupError("DNS lookup failed for %s" % name))
                return succeed(self.lookups[name])
        self.nameResolver = SimpleResolverComplexifier(FakeResolver())
        super().__init__()
    def installNameResolver(self, resolver: IHostnameResolver) -> IHostnameResolver:
        raise NotImplementedError