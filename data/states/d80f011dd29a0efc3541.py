from flask import Flask, request, redirect
import os
import sys

app = Flask(__name__)

@app.route('/url/ping')
def ping():
    url = request.args.get('url')
    if not url:
        return "Missing url", 400
    import subprocess
    try:
        result = subprocess.run(
            ["ping", "-c1", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=5,
            text=True
        )
        return result.stdout
    except subprocess.SubprocessError as e:
        return str(e), 500
    except Exception as e:
        return str(e), 500