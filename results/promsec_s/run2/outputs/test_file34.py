import json
from io import BytesIO
import logging
import os
import attr
from six import text_type
from twisted.internet import address
import twisted.logger
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto

FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEbG9vZzANBgkqhkiG9w0BAQsFADBvMQswCQYDVQQGEwJV
UzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCk1vdW50YWluIFZpZXcxFjAUBgNVBAoT
DVN5ZG50IHRlc3QgQ0ExGDAWBgNVBAMTD3d3dy5leGFtcGxlLmNvbTAeFw0xNDA1
MTkwMDAwMDBaFw0yNDA1MTkwMDAwMDBaMG8xCzAJBgNVBAYTAlVTMQswCQYDVQQI
EwJDQTESMBAGA1UEBxMJTW91bnRhaW4gVmlldzEWMBQGA1UEChMNU3lkZW50IHRl
c3QgQ0ExGDAWBgNVBAMTD3d3dy5leGFtcGxlLmNvbTCCASIwDQYJKoZIhvcNAQEB
BQADggEPADCCAQoCggEBAL6V6wX6Z1GDZCBoBPXaGNsq4CPGK/c/pX9nuSUXwxLB
cg2YkdE+5EYXPLkZX31lrT7xvFeoJEB6Digw1VE3D6Z0SqnX+0Gooy2cwr6jciJ6
2PzefRg2fzGEGZm4G6dkprdFM5lTyBC0bYKT1eZq9VHtV6nRvWmvMRGsiE9z1FM3
bMpiKFFitvolG/G5hgbf+5Q5e0M1Vo9hw3rroWAtxEvsC0BpvyEukgqS0bkkCm1c
G5kyRjO6jwxKF1u9IiMaivGi99ZTSdKCbFf8gDuwZQzQ0jrISFRCGDpa2BkLomPv
j0vvVuv5AO9M/dwZ0pniS3pSke1Mt2rt7NmBGG99nm8CAwEAAaNQME4wHQYDVR0O
BBYEFAaKBslZx2drXr/7EQo1gChX2NDVMB8GA1UdIwQYMBaAFAaKBslZx2drXr/7
EQo1gChX2NDVMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBABw9u5lH
ZArYdS4x+h0cYfZcQ3VIAtF5NCz7L+G5kZZgwyU0YzUKGwEuKXXSb9VjA36TObgG
OJe7E5Wdl0iRS0LlwM1c01qmPvvrLpzjAU6YewsGQKzBSSMSmc5QwDFi1Cdm42BC
tyi1zBcY9qsK0kGugHgd6NqBJ38qRAjPR9U1FVLtZL1NVr7Di5urN6byN1Nsx3Rp
1Ian+FJxuxMxDPZWS9Vyuk3F7S3w7Dnk3a1JpN96CBvs1+qsYqSdz+CA0nVddOcx
6jttuPAHyBs+K6TfGsDz3jAC5vVsQt1zArhcXd1LSeXfhBF3/f6/Dr7guP5AnbcW
CYwiVdc+GqY=
-----END CERTIFICATE-----"""

def make_sydent(test_config={}):
    """Create a Sydent instance for testing.

    Parameters
    ----------
    test_config : dict, optional
        Configuration overrides for the Sydent instance.

    Returns
    -------
    Sydent
        A configured Sydent instance using an in‑memory SQLite database
        unless overridden.
    """
    from sydent.sydent import Sydent, parse_config_dict
    cfg = dict(test_config)
    if 'database' not in cfg:
        cfg['database'] = {'type': 'sqlite3', 'args': ':memory:'}
    reactor = MemoryReactorClock()
    return Sydent(reactor=reactor, cfg=parse_config_dict(cfg))

@attr.s
class FakeChannel:
    site = attr.ib(type=Site)
    _reactor = attr.ib()
    result = attr.ib(factory=dict)
    _producer = attr.ib(default=None)

    @property
    def json_body(self):
        if not self.result:
            raise RuntimeError("No result available")
        body = self.result.get('body', b'')
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        return json.loads(body)

    @property
    def code(self):
        if not self.result:
            raise RuntimeError("No result available")
        return int(self.result['code'])

    @property
    def headers(self):
        if not self.result:
            raise RuntimeError("No result available")
        return Headers(self.result['headers'])

    def writeHeaders(self, code, headers):
        if not isinstance(code, int):
            raise TypeError("code must be int")
        if not isinstance(headers, dict):
            raise TypeError("headers must be dict")
        self.result['code'] = code
        self.result['headers'] = headers

    def write(self, data):
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")
        self.result.setdefault('body', b'')
        self.result['body'] += data

    def registerProducer(self, producer, streaming):
        self._producer = producer

    def unregisterProducer(self):
        self._producer = None

    def requestDone(self):
        pass

    def getPeer(self):
        return address.IPv4Address('TCP', '127.0.0.1', 12345)

    def getHost(self):
        return address.IPv4Address('TCP', '127.0.0.1', 80)

    @property
    def transport(self):
        return self

    def getPeerCertificate(self):
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM.encode('utf-8'))

class FakeSite:
    """A fake Twisted Web Site."""
    pass

def make_request(reactor, method, path, content=b"", access_token=None, request=Request, shorthand=True, federation_auth_origin=None):
    """Create a Twisted Request object for testing.

    Parameters
    ----------
    reactor : twisted.internet.reactor.IReactorTime
        The reactor to use.
    method : bytes or str
        HTTP method.
    path : bytes or str
        Request path.
    content : bytes, dict, or six.text_type, optional
        Request body.
    access_token : str, optional
        Bearer token for Authorization header.
    request : class, optional
        Request class to instantiate.
    shorthand : bool, optional
        Whether to prepend the identity API prefix.
    federation_auth_origin : bytes or str, optional
        Federation authentication origin.

    Returns
    -------
    tuple
        (request, channel) pair.
    """
    if not isinstance(method, bytes):
        method = method.encode('utf-8')
    if not isinstance(path, bytes):
        path = path.encode('utf-8')
    if shorthand and not path.startswith(b"/_matrix"):
        path = b"/_matrix/identity/v2/" + path.lstrip(b"/")
        while b"//" in path:
            path = path.replace(b"//", b"/")
    if not path.startswith(b"/"):
        path = b"/" + path
    if isinstance(content, dict):
        content = json.dumps(content).encode('utf-8')
    elif isinstance(content, text_type):
        content = content.encode('utf-8')
    site = FakeSite()
    channel = FakeChannel(site, reactor)
    req = request(channel)
    req.process = lambda: b""
    req.content = BytesIO(content)
    decoded_path = unquote(path)
    req.postpath = [segment for segment in decoded_path.split(b"/") if segment]
    if access_token is not None:
        header_value = b"Bearer " + access_token.encode('utf-8')
        req.requestHeaders.addRawHeader(b"Authorization", header_value)
    if federation_auth_origin is not None:
        if not isinstance(federation_auth_origin, bytes):
            federation_auth_origin = federation_auth_origin.encode('utf-8')
        header_value = b"X-Matrix origin=%s,key=,sig=" % federation_auth_origin
        req.requestHeaders.addRawHeader(b"Authorization", header_value)
    if content:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method, path, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    tx_log = twisted.logger.Logger(namespace="sydent")
    def emit(self, record):
        log_entry = self.format(record)
        log_level = record.levelname.lower()
        if log_level == "warning":
            log_level = "warn"
        level = twisted.logger.LogLevel.levelWithName(log_level)
        self.tx_log.emit(level, "{entry}", entry=log_entry)

def setup_logging():
    root = logging.getLogger()
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    handler = ToTwistedHandler()
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)
    level_name = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR")
    root.setLevel(level_name)

try:
    setup_logging()
except Exception as e:
    logging.getLogger().warning("Logging setup failed: %s", e)