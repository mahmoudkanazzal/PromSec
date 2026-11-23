import json
from io import BytesIO
import logging
import os
import attr
from six import text_type
from twisted.internet import address
from twisted.web.http_headers import Headers
from twisted.web.server import Request, Site
from twisted.web.http import unquote
from twisted.test.proto_helpers import MemoryReactorClock
from OpenSSL import crypto
from sydent.sydent import Sydent, parse_config_dict
from twisted.logger import Logger, LogLevel

FAKE_SERVER_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEbG9vZzANBgkqhkiG9w0BAQsFADBvMQswCQYDVQQGEwJV
UzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCk1vdW50YWluIFZpZXcxFjAUBgNVBAoT
DVN5ZG50IEV4YW1wbGUxFjAUBgNVBAsTDUlUIERlcGFydG1lbnQxEzARBgNVBAMT
Ck15IENlcnQgQ0EwHhcNMjAwMTAxMDAwMDAwWhcNMzAwMTAxMDAwMDAwWjBvMQsw
CQYDVQQGEwJVUzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCk1vdW50YWluIFZpZXcx
FjAUBgNVBAoTDVN5ZG50IEV4YW1wbGUxFjAUBgNVBAsTDUlUIERlcGFydG1lbnQx
EzARBgNVBAMTCk15IENlcnQgQ0EwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQC7V6p9K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6x
V6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6
Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K
5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZc
K6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV
6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Z
c6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5
vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK
6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6
V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc
6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5v
ZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V
6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6
K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZ
cK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6xV6V6Zc6K5vZcK6
VQ==
-----END CERTIFICATE-----"""

def make_sydent(test_config=None):
    if test_config is None:
        test_config = {}
    db_cfg = test_config.setdefault("db", {})
    db_cfg.setdefault("db.file", ":memory:")
    reactor = MemoryReactorClock()
    return Sydent(reactor, parse_config_dict(test_config))

@attr.s
class FakeChannel:
    site = attr.ib()
    _reactor = attr.ib()
    result = attr.ib(factory=dict)
    _producer = attr.ib(default=None)

    @property
    def json_body(self):
        if not self.result:
            raise ValueError("No result")
        body = self.result.get("body", b"")
        return json.loads(body.decode("utf-8"))

    @property
    def code(self):
        if not self.result:
            raise ValueError("No result")
        return int(self.result["code"])

    @property
    def headers(self):
        if not self.result:
            raise ValueError("No result")
        return Headers(self.result["headers"])

    def writeHeaders(self, version, code, reason, headers):
        self.result["version"] = version
        self.result["code"] = code
        self.result["reason"] = reason
        self.result["headers"] = headers

    def write(self, content):
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError("content must be bytes")
        self.result["body"] = self.result.get("body", b"") + content

    def registerProducer(self, producer, streaming):
        self._producer = producer
        if not streaming:
            self._reactor.callLater(0, producer.resumeProducing)
        else:
            producer.resumeProducing()

    def unregisterProducer(self):
        self._producer = None

    def requestDone(self, _self):
        self.result["done"] = True

    def getPeer(self):
        return address.IPv4Address("TCP", "127.0.0.1", 3423)

    def getHost(self):
        return None

    @property
    def transport(self):
        return self

    def getPeerCertificate(self):
        return crypto.load_certificate(crypto.FILETYPE_PEM, FAKE_SERVER_CERT_PEM.encode())

class FakeSite(Site):
    pass

def make_request(reactor, method, path, content=b"", access_token=None, request=Request, shorthand=True, federation_auth_origin=None):
    if isinstance(method, text_type):
        method = method.encode("utf-8")
    if isinstance(path, text_type):
        path = path.encode("utf-8")
    if shorthand and not path.startswith(b"/_matrix"):
        path = b"/_matrix/identity/v2/" + path.lstrip(b"/")
        while b"//" in path:
            path = path.replace(b"//", b"/")
    if not path.startswith(b"/"):
        path = b"/" + path
    if isinstance(content, dict):
        body_bytes = json.dumps(content).encode("utf-8")
    elif isinstance(content, text_type):
        body_bytes = content.encode("utf-8")
    else:
        body_bytes = content
    site = FakeSite()
    channel = FakeChannel(site, reactor)
    req = request(channel)
    req.process = lambda: b""
    req.content = BytesIO(body_bytes)
    req.postpath = [unquote(seg) for seg in path.split(b"/") if seg]
    if access_token is not None:
        token_bytes = access_token.encode("utf-8") if isinstance(access_token, text_type) else access_token
        req.requestHeaders.addRawHeader(b"Authorization", b"Bearer " + token_bytes)
    if federation_auth_origin is not None:
        origin = federation_auth_origin.encode("utf-8") if isinstance(federation_auth_origin, text_type) else federation_auth_origin
        header_val = b"X-Matrix origin=" + origin + b",key=,sig="
        req.requestHeaders.addRawHeader(b"Authorization", header_val)
    if body_bytes:
        req.requestHeaders.addRawHeader(b"Content-Type", b"application/json")
    req.requestReceived(method, path, b"1.1")
    return req, channel

class ToTwistedHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.tx_log = Logger()

    def emit(self, record):
        log_entry = self.format(record)
        level_name = record.levelname.lower().replace("warning", "warn")
        level = LogLevel.levelWithName(level_name)
        self.tx_log.emit(level, "{entry}", entry=log_entry)

def setup_logging():
    root = logging.getLogger()
    fmt = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    handler = ToTwistedHandler()
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)
    level_str = os.getenv("SYDENT_TEST_LOG_LEVEL", "ERROR").upper()
    root.setLevel(getattr(logging, level_str, logging.ERROR))

if __name__ == "__main__":
    setup_logging()