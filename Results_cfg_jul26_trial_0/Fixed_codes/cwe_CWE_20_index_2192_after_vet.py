import os
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor
import logging

logging.basicConfig(filename='server.log', level=logging.INFO)

class HelloWorld(Resource):
    isLeaf = True

    def render_GET(self, request):
        logging.info(f"Received GET request from {request.getClientIP()}")
        return b"Hello, World!"

root = Resource()
root.putChild(b"", HelloWorld())
factory = Site(root)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    reactor.listenTCP(port, factory)
    logging.info(f"Server started on port {port}")
    reactor.run()