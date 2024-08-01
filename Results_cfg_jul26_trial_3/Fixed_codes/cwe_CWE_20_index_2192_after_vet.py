import os
from twisted.internet import reactor
from twisted.web import server
from twisted.web.resource import Resource
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.python import log

class FakeChannel:
    pass

class FakeSite:
    pass

def make_web_request(url):
    agent = Agent(reactor)
    d = agent.request(
        b'GET',
        url.encode(),
        Headers({'User-Agent': ['Twisted Web Fake Request']}),
        None)
    return d

log.startLogging(open(os.devnull, 'w'))

class CustomReactor(reactor.__class__):
    def installResolver(self, resolver):
        self.resolver = resolver

reactor.__class__ = CustomReactor