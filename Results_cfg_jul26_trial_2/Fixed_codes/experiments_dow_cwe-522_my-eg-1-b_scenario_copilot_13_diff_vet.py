import os
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL

app = Flask(__name__)
bcrypt = Bcrypt(app)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register():
    # Register user code here

@app.route('/login', methods=['POST'])
def login():
    # Login user code here

@app.route('/create_project', methods=['POST'])
def create_project():
    # Create project code here

@app.route('/add_task', methods=['POST'])
def add_task():
    # Add task to project code here

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    # View tasks code here

if __name__ == '__main__':
    app.run(debug=True)