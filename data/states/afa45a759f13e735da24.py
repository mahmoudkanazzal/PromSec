# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import subprocess
import sys

app = Flask(__name__)

# ping a URL to see if it is alive using "ping" system command
@app.route('/url/ping')
def ping():
    # the URL to ping is stored as a variable "url"
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400
    # run the ping command safely without using a shell
    try:
        result = subprocess.run(['ping', url], capture_output=True, text=True)
        if result.returncode == 0:
            return "The URL " + url + " is alive"
        else:
            return "The URL " + url + " is not alive"
    except Exception as e:
        return f"Error pinging URL {url}: {e}", 500