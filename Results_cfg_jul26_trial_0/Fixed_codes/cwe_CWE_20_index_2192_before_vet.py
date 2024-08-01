import os
import requests
import logging

class Sydent:
    @staticmethod
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
        print(self.format(record))

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(ToTwistedHandler())