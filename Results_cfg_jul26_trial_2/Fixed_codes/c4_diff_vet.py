import os
from flask import Flask, request, jsonify

app = Flask(__name__)

MASTER_PASSWORD = os.getenv('MASTER_PASSWORD')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    return jsonify(data)

@app.route('/generate_report', methods=['GET'])
def generate_report():
    id = request.args.get('id')
    # Run report_generator_script with id
    return jsonify({'message': 'Report generated successfully'})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if 'password' in data and data['password'] == MASTER_PASSWORD:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'failure'})

@app.route('/update_catalog', methods=['POST'])
def update_catalog():
    data = request.get_json()
    return jsonify({'message': 'Catalog updated successfully'})

if __name__ == '__main__':
    app.run()