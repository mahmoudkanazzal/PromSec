import os
import logging
import requests
from sydent.sydent import Sydent

def make_sydent():
    sydent = Sydent(os.getenv('SYDENT_HOST'), os.getenv('SYDENT_PORT'))
    return sydent

class FakeChannel:
    def __init__(self, sydent):
        self.sydent = sydent

def make_request(method, url, data=None):
    response = requests.request(method, url, data=data)
    return response

class FakeSite:
    def __init__(self, sydent):
        self.sydent = sydent

class ToTwistedHandler(logging.Handler):
    def emit(self, record):
        pass

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = ToTwistedHandler()
    logger.addHandler(handler)