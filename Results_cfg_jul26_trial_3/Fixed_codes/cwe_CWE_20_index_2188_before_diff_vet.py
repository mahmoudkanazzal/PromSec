import os
import requests
import logging

class Sydent:
    pass

def make_sydent():
    return Sydent()

class FakeChannel:
    pass

def make_request(url, data):
    return requests.post(url, data)

class FakeSite:
    pass

class ToTwistedHandler(logging.Handler):
    def emit(self, record):
        pass

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ToTwistedHandler())

fake_tls_cert = """
-----BEGIN CERTIFICATE-----
MIIDozCCAougAwIBAgIJAJ7z1z1z1z1zMA0GCSqGSIb3DQEBCwUAMIGUMQswCQYD
VQQGEwJVUzELMAkGA1UECAwCTUExEDAOBgNVBAcMB0JyaXN0b2wxEDAOBgNVBAoM
B0Zha2UgTWFuMQwwCgYDVQQLDANPQkExDDAKBgNVBAMMA0Jsb2UxGDAWBgkqhkiG
9w0BCQEWCWxvZUBnbWFpbC5jb20wHhcNMTkwNjI4MTQ1MzQwWhcNMjkwNjI1MTQ1
MzQwWjCBkDELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAk1BMRAwDgYDVQQHDAdCcmlz
dG9sMRAwDgYDVQQKDAdGYWtlIE1hbjEMMAoGA1UECwwDT0JBMQwwCgYDVQQDDANC
bG9lMRgwFgYJKoZIhvcNAQkBFglsb2VAZ21haWwuY29tMIIBIjANBgkqhkiG9w0B
AQEFAAOCAQ8AMIIBCgKCAQEAz5zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3z
v3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3z
v3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3z
v3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3z
v3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3z
v3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3zv3z