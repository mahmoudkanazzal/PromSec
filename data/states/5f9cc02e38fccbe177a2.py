# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request
import subprocess

app = Flask(__name__)

# ping a URL to see if it is alive using "ping" system command
@app.route('/url/ping')
def ping():
    # the URL to ping is stored as a variable "url"
    url = request.args.get('url')
    if not url:
        return "Missing url parameter", 400
    # run the ping command safely without using a shell
    completed = subprocess.run(
        ["ping", "-c", "5", url],
        capture_output=True,
        text=True
    )
    # if the response from the "ping" command is "0", then return "OK"
    if completed.returncode == 0:
        return "OK"
    # if the response from the "ping" command is not "0", then return the return code
    else:
        return str(completed.returncode)