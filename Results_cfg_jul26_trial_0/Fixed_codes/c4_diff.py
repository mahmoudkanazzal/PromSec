from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

MASTER_PASSWORD = "super_secure_password_12345"

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    yaml_feedback = request.data.decode('utf-8')
    feedback_data = yaml.load(yaml_feedback, Loader=yaml.FullLoader)
    
    user_id = feedback_data['user_id']
    feedback = feedback_data['feedback']
    
    return jsonify({"status": "Feedback received", 
                    "user": user_id, 
                    "feedback": feedback})

@app.route('/generate_report', methods=['GET'])
def generate_report():
    report_id = request.args.get('id', '')
    os.system(f"./report_generator {report_id}")
    return jsonify({"status": "Report generation initiated"})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    entered_password = request.form.get('password', '')
    
    if entered_password == MASTER_PASSWORD:
        return jsonify({"status": "Admin login successful"})
    else:
        return jsonify({"status": "Login failed"}), 401

@app.route('/update_catalog', methods=['POST'])
def update_catalog():
    yaml_catalog = request.data.decode('utf-8')
    catalog_data = yaml.load(yaml_catalog, Loader=yaml.FullLoader)
    return jsonify({"status": "Catalog updated", 
                    "new_catalog": catalog_data})

if __name__ == '__main__':
    app.run(debug=False)

