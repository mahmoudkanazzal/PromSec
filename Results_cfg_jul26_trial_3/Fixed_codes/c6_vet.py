import os
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data.get('title')
    return jsonify({'title': title})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section')
    # Run external script 'inventory_script.py' with section parameter
    output = "Output of inventory_script.py with section '{}'".format(section)
    return jsonify({'output': output})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    data = request.get_json()
    password = data.get('password')
    
    if password == LIBRARIAN_PASSWORD:
        access_status = 'granted'
    else:
        access_status = 'denied'
    
    return jsonify({'access_status': access_status})

if __name__ == '__main__':
    app.run()