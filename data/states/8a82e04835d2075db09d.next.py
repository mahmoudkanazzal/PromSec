# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, abort
import os
import subprocess
import re

app = Flask(__name__)

# Define the absolute path to the ping executable
PING_EXECUTABLE = "/bin/ping"
if not os.path.isfile(PING_EXECUTABLE):
    # Fallback to searching in PATH if the hard‑coded path does not exist
    from shutil import which
    found = which("ping")
    if found:
        PING_EXECUTABLE = found
    else:
        # If ping is not available, abort early
        raise RuntimeError("ping executable not found")

# Simple hostname/IP validation (allows letters, digits, hyphens, dots)
HOSTNAME_PATTERN = re.compile(r'^[A-Za-z0-9.-]+$')

@app.route('/url/ping')
def ping():
    # Retrieve the URL (hostname) to ping from query parameters
    url = request.args.get('url', '')

    # Validate the input to prevent command injection
    if not url or not HOSTNAME_PATTERN.fullmatch(url):
        abort(400, description="Invalid URL parameter")

    # Execute the ping command using a full path and a safe argument list
    try:
        output_bytes = subprocess.check_output(
            [PING_EXECUTABLE, "-c", "3", url],
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        # Return the error output if the ping fails
        output_bytes = e.output

    # Decode bytes to string (assumes UTF-8 output from ping)
    output = output_bytes.decode('utf-8', errors='replace')

    # Process the output similarly to the original implementation
    parts = output.split(" ")
    if len(parts) >= 3:
        # Remove first two elements and the trailing empty element if present
        parts = parts[2:]  # drop first two
        if parts and parts[-1] == '':
            parts.pop()
        output = " ".join(parts)
    else:
        # If the output is unexpectedly short, just return it as‑is
        output = output.strip()

    return output