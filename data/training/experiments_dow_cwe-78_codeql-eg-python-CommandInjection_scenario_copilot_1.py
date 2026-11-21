from flask import Flask, request, redirect, jsonify
import subprocess
import validators

app = Flask(__name__)

@app.route('/url/ping')
def ping():
    # Get the URL from the 'url' query parameter
    url = request.args.get('url')

    # Validate that a URL was provided and is properly formatted
    if url is None or not validators.url(url):
        return jsonify({'error': 'Invalid or missing URL'}), 400

    # Extract the hostname from the URL (e.g., example.com from https://example.com/some/path)
    hostname = url.split('//')[-1].split('/')[0]

    try:
        # Use the more secure subprocess.run() to execute the ping command without shell interpretation
        # Here, we're limiting the count to 1 ping request for quick response
        completed_process = subprocess.run(['ping', '-c', '1', hostname], capture_output=True, text=True, check=True)

        # Check if the command was successful
        if completed_process.returncode == 0:
            return redirect(url)
        else:
            return jsonify({'error': 'Ping failed'}), 500
    except subprocess.CalledProcessError as e:
        # Handle the error in a manner appropriate for your application
        return jsonify({'error': 'Ping command failed with an error: ' + str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred: ' + str(e)}), 500

