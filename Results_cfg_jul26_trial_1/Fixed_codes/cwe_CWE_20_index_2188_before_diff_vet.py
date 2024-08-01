import os
import logging
import requests

def make_sydent():
    pass

class FakeChannel:
    def __init__(self):
        pass

def make_request(url, data):
    pass

class FakeSite:
    def __init__(self):
        pass

class ToTwistedHandler(logging.Handler):
    def emit(self, record):
        pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(ToTwistedHandler())