import os
import logging
import requests
from sydent import Sydent

def make_sydent():
    return Sydent()

class FakeChannel:
    pass

def make_request(url, data, headers):
    return requests.post(url, data=data, headers=headers)

class FakeSite:
    pass

class ToTwistedHandler(logging.Handler):
    def emit(self, record):
        pass

def setup_logging():
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().addHandler(ToTwistedHandler())