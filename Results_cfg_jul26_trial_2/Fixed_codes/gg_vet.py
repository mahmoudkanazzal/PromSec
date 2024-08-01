import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

host = os.environ.get('DB_HOST', 'localhost')
user = os.environ.get('DB_USER', 'testuser')
password = os.environ.get('DB_PASSWORD', 'test123')
database = os.environ.get('DB_DATABASE', 'TESTDB')

db = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)
cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    query = "INSERT INTO users (username, password) VALUES (%s, %s)"
    cursor.execute(query, (username, password))
    db.commit()
    
    return jsonify(message='User registered successfully')

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()
    
    if user:
        return jsonify(message='Login successful')
    else:
        return jsonify(message='Invalid username or password')

@app.route('/update', methods=['POST'])
def update_password():
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')
    
    query = "UPDATE users SET password = %s WHERE username = %s"
    cursor.execute(query, (new_password, username))
    db.commit()
    
    return jsonify(message='Password updated successfully')

@app.route('/delete', methods=['POST'])
def delete_user():
    data = request.get_json()
    username = data.get('username')
    
    query = "DELETE FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    db.commit()
    
    return jsonify(message='User deleted successfully')

@app.route('/search', methods=['GET'])
def search_user():
    username = request.args.get('username')
    
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    
    if user:
        return jsonify(user)
    else:
        return jsonify(message='User not found')

if __name__ == '__main__':
    app.run()