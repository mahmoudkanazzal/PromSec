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
        Headers({'User-Agent': ['Twisted Web Client Example']}),
        None)
    return d

log.startLogging(open('sydent.log', 'w'))

reactor.installResolver(FakeResolver())

reactor.run()