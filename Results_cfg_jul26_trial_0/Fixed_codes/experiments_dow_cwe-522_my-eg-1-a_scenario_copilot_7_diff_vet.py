import MySQLdb
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

db = MySQLdb.connect(host="localhost", user="testuser", passwd="test123", db="EMPDB")
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register_user():
    # Register user code here

@app.route('/login', methods=['POST'])
def login_user():
    # Login user code here

@app.route('/employees', methods=['GET', 'POST'])
def employees():
    # Get or add employees code here

@app.route('/employees/<employee_id>', methods=['PUT', 'DELETE'])
def update_delete_employee(employee_id):
    # Update or delete employee code here

@app.route('/departments', methods=['GET', 'POST'])
def departments():
    # Get or add departments code here

@app.route('/projects', methods=['GET', 'POST'])
def projects():
    # Get or add projects code here

if __name__ == '__main__':
    app.run()
