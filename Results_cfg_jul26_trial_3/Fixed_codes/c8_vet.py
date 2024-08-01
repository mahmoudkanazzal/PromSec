import os
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['DEBUG'] = False

SECRET_ADMIN_PASS = os.getenv('SECRET_ADMIN_PASS')

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    data = request.get_json()
    return jsonify(data)

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section')
    return f'Executing inventory for section: {section}'

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password')
    if password == SECRET_ADMIN_PASS:
        return 'Access granted'
    else:
        return 'Access denied'

if __name__ == '__main__':
    app.run()
