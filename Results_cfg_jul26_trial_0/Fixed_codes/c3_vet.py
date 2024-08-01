import os
from flask import Flask, request, jsonify

app = Flask(__name__)

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if 'password' in data and data['password'] == ADMIN_PASSWORD:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Login failed'})

@app.route('/create_post', methods=['POST'])
def create_post():
    data = request.get_json()
    return jsonify(data)

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')
    status = os.system(f'./generate_report.sh {report_type}')
    if status == 0:
        return jsonify({'message': 'Report generated successfully'})
    else:
        return jsonify({'message': 'Report generation failed'})

if __name__ == '__main__':
    app.run()