# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import subprocess
import sys
import re
import shutil

app = Flask(__name__)

def _is_valid_host(host: str) -> bool:
    """
    Validate that the provided host contains only allowed characters
    for a hostname or IP address.
    """
    return bool(re.fullmatch(r"[A-Za-z0-9.\-]+", host or ""))

@app.route('/url/ping')
def ping():
    # Retrieve the URL (host) to ping from query parameters
    url = request.args.get('url', '')

    # Validate the input to prevent misuse of the ping command
    if not _is_valid_host(url):
        return "Invalid host", 400

    # Resolve the full path to the ping executable to avoid partial path issues
    ping_executable = shutil.which("ping")
    if not ping_executable:
        return "Ping executable not found", 500

    # Execute the ping command safely without invoking a shell
    try:
        output_bytes = subprocess.check_output([ping_executable, "-c", "3", url], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return f"Ping failed: {e.output.decode(errors='ignore')}", 500

    # Decode and process the output
    output = output_bytes.decode(errors='ignore')
    parts = output.split(" ")
    # Remove first two elements and the trailing empty element if present
    if len(parts) >= 3:
        parts = parts[2:]  # drop first two
    if parts and parts[-1] == "":
        parts.pop()
    # Join the remaining parts
    result = " ".join(parts)
    return result