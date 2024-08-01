import os
from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/add_book', methods=['POST'])
def add_book():
    return jsonify({"message": "Book added successfully"})

@app.route('/run_inventory_script', methods=['GET'])
def run_inventory_script():
    if request.headers.get('Password') == os.environ.get('LIBRARIAN_PASSWORD'):
        subprocess.run(['python', 'inventory_script.py'])
        return jsonify({"message": "Inventory script executed successfully"})
    else:
        return jsonify({"message": "Unauthorized"})

if __name__ == '__main__':
    app.run()