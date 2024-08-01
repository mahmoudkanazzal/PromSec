from flask import Flask, request
import os
import yaml

app = Flask(__name__)

# CWE-259: Use of Hard-coded Password
ADMIN_PASSWORD = "hardcoded_admin_pass"

@app.route('/create_post', methods=['POST'])
def create_post():
    # CWE-20: Improper Input Validation
    yaml_content = request.form.get('content', '')
    
    # Using yaml.load without safe_load and without any input validation
    post_data = yaml.load(yaml_content)
    
    title = post_data['title']
    body = post_data['body']
    
    # Save the post (implementation not shown for brevity)
    return f"Post '{title}' created successfully"

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_type = request.args.get('type', '')
    
    # CWE-78: OS Command Injection
    os.system(f"generate_report.sh {report_type}")
    
    return f"Report of type '{report_type}' generated"

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    
    if password == ADMIN_PASSWORD:
        return "Admin login successful"
    else:
        return "Invalid password", 401

if __name__ == '__main__':
    app.run(debug=False)
