import os
from twisted.internet import reactor, ssl
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.web import server
from twisted.python import log
from twisted.internet.endpoints import SSL4ServerEndpoint
from twisted.internet.ssl import DefaultOpenSSLContextFactory
from twisted.web.client import Agent
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import react
from twisted.internet.task import deferLater
from twisted.internet.task import Clock

class Sydent:
    def __init__(self):
        pass

class FakeChannel:
    def __init__(self):
        pass

def make_web_request(url):
    pass

class MemoryReactorClock(Clock):
    def __init__(self):
        pass

log.startLogging(open('twisted.log', 'w'))

root = Resource()
root.putChild(b"static", File("/var/www"))

site = Site(root)
reactor.listenTCP(8080, site)

reactor.run()