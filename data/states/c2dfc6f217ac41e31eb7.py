# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import subprocess
import sys

app = Flask(__name__)

# ping a URL to see if it is alive using "ping" system command
@app.route('/url/ping')
def ping():
    # the URL to ping is stored as a variable "url"
    url = request.args.get('url', '')
    if not url:
        return 'Missing url parameter', 400
    try:
        # Run ping without using a shell to avoid injection risks
        result = subprocess.run(
            ['ping', '-c1', url],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Return stdout on success, otherwise return stderr
        return result.stdout if result.returncode == 0 else result.stderr, 200
    except Exception as e:
        return str(e), 500