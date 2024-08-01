import os
import requests
import logging

class Sydent:
    def __init__(self, db_path, config_path):
        self.db_path = db_path
        self.config_path = config_path
    
    @staticmethod
    def make_sydent(db_path, config_path):
        return Sydent(db_path, config_path)

class FakeChannel:
    def __init__(self, sydent_instance):
        self.sydent_instance = sydent_instance

def make_request(url, data):
    response = requests.post(url, data=data)
    return response

class FakeSite:
    def __init__(self, sydent_instance):
        self.sydent_instance = sydent_instance

class ToTwistedHandler(logging.Handler):
    def emit(self, record):
        pass

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(ToTwistedHandler())