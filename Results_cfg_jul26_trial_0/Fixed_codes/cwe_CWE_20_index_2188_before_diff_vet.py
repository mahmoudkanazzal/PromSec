import os
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.channel import HTTPChannel
from twisted.python import log

class FakeChannel(HTTPChannel):
    pass

class FakeSite(Site):
    protocol = FakeChannel

def send_logs_to_twisted_log(msg):
    log.msg(msg)

def make_web_request(method, path, content=None, access_token=None, federation_auth_origin=None):
    # Make web request using Twisted
    pass

if __name__ == "__main__":
    # Set up logging handler
    log.startLoggingWithObserver(send_logs_to_twisted_log, setStdout=False)

    # Set up Sydent server
    root = Resource()
    site = FakeSite(root)
    reactor.listenTCP(8080, site)

    # Start the reactor
    reactor.run()