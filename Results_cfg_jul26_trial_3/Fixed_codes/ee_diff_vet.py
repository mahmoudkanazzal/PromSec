import os
from flask import Flask, request, jsonify
import MySQLdb

app = Flask(__name__)

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'cisco123'
DB_NAME = 'task_manager'

db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register_user():
    # Register user code here

@app.route('/login', methods=['POST'])
def login_user():
    # Login user code here

@app.route('/add_task', methods=['POST'])
def add_task():
    # Add task code here

@app.route('/view_tasks', methods=['GET'])
def view_tasks():
    # View tasks code here

@app.route('/delete_task', methods=['DELETE'])
def delete_task():
    # Delete task code here

@app.route('/update_task', methods=['PUT'])
def update_task():
    # Update task code here

if __name__ == '__main__':
    app.run()
