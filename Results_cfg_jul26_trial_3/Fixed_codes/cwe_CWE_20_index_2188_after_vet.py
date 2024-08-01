import os
import logging

os.environ['SECRET_KEY'] = 'my_secret_key'
os.environ['PASSWORD'] = 'my_password'

logging.basicConfig(level=logging.INFO)

class WebRequest:
    def handle_response(self, response):
        print_response(response)

    def make_request(self, url):
        print(f'Making request to {url}')

class ResponseHandler:
    def dataReceived(self, data):
        print_response(data)

    def connectionLost(self):
        print_error('Connection lost')

def print_response(message):
    logging.info(f'Response: {message}')

def print_error(message):
    logging.error(f'Error: {message}')

if __name__ == '__main__':
    web_request = WebRequest()
    response_handler = ResponseHandler()

    web_request.make_request('https://example.com')
    response_handler.dataReceived('Data received')
    response_handler.connectionLost()