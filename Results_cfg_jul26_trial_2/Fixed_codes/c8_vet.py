import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    data = request.get_json()
    return jsonify(data)

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section')
    os.system(f'python run_inventory.py {section}')
    return 'Inventory executed for section: {}'.format(section)

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password')
    secret_admin_pass = os.getenv('SECRET_ADMIN_PASS')
    if password == secret_admin_pass:
        return 'Admin access granted'
    else:
        return 'Incorrect password'

if __name__ == '__main__':
    app.run()
