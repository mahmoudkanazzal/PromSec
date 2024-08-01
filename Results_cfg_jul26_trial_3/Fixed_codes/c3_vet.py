import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/create_post', methods=['POST'])
def create_post():
    return jsonify({'message': 'Post created successfully'})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data['password'] == os.environ.get('ADMIN_PASSWORD'):
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Login failed'})

@app.route('/generate_report', methods=['POST'])
def generate_report():
    data = request.get_json()
    parameter = data['parameter']
    os.system(f'./generate_report.sh {parameter}')
    return jsonify({'message': 'Report generated'})

if __name__ == '__main__':
    app.run()
