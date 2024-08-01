import os
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet.ssl import CertificateOptions
from twisted.python import log
from twisted.internet.task import LoopingCall
from twisted.internet.testing import MemoryReactorClock

class SydentServer:
    def __init__(self):
        self.reactor = reactor
        self.clock = FakeMemoryReactorClock()
        self.agent = Agent(reactor)
        self.site = FakeTwistedWebSite()
        self.channel = FakeTwistedWebChannel()
    
    def start(self):
        self.reactor.run()

class FakeTwistedWebChannel:
    pass

class FakeTwistedWebSite(Resource):
    pass

def make_web_request(url):
    agent = Agent(reactor)
    d = agent.request(
        b'GET',
        url.encode('utf-8'),
        Headers({'User-Agent': ['Twisted Web Client Example']}),
        None)
    return d

class FakeMemoryReactorClock(MemoryReactorClock):
    def __init__(self):
        super().__init__()
    
    def resolve(self, name, timeout=None):
        return name

log.startLogging(open('sydent.log', 'w'))

tls_cert = """
-----BEGIN CERTIFICATE-----
MIICpDCCAYwCCQDq7J6Q7Q6QkDANBgkqhkiG9w0BAQsFADASMRAwDgYDVQQDDAdG
YWtlIFNlcnZlcjAeFw0yMTA0MTYxNzQwMzBaFw0zMTA0MTYxNzQwMzBaMBIxEDAO
BgNVBAMMB0Zha2UgU2VydmVyMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQ
EAt1Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Z
z5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Z
z5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Z
z5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Z
z5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5Zz5