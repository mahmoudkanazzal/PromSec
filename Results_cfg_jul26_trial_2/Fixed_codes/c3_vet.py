import os
from flask import Flask, request, jsonify

app = Flask(__name__)

HARDCODED_ADMIN_PASS = os.getenv('HARDCODED_ADMIN_PASS')

@app.route('/create_post', methods=['POST'])
def create_post():
    data = request.get_json()
    title = data.get('title')
    body = data.get('body')
    
    # Process the data
    
    return jsonify({'message': 'Post created successfully'})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type')
    
    # Execute shell script with report_type
    
    return jsonify({'message': 'Report generated successfully'})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    password = data.get('password')
    
    if password == HARDCODED_ADMIN_PASS:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Login failed'})

if __name__ == '__main__':
    app.run()