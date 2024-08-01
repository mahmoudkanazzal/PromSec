import os
from flask import Flask, request, jsonify

app = Flask(__name__)

SECRET_ADMIN_PASS = os.getenv('SECRET_ADMIN_PASS')

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    data = request.get_json()
    return jsonify(data)

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section')
    os.system(f'python run_inventory.py {section}')
    return jsonify({'message': 'Inventory executed successfully'})

@app.route('/admin_access', methods=['POST'])
def admin_access():
    data = request.get_json()
    if 'password' in data and data['password'] == SECRET_ADMIN_PASS:
        return jsonify({'message': 'Admin access granted'})
    else:
        return jsonify({'message': 'Admin access denied'})

if __name__ == '__main__':
    app.run()