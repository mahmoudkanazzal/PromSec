import os
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = 'mydatabase'

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
    # Add task code here

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    # View tasks code here

if __name__ == '__main__':
    app.run(debug=True)
