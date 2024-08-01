import os
from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

host = os.environ.get('DB_HOST', 'localhost')
user = os.environ.get('DB_USER', 'root')
passwd = os.environ.get('DB_PASS', 'password')
db = os.environ.get('DB_NAME', 'cwe_900')

def get_db_connection():
    return mysql.connector.connect(
        host=host,
        user=user,
        passwd=passwd,
        db=db
    )

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET password = %s WHERE username = %s", (new_password, username))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({'message': 'Profile updated successfully'})

@app.route('/search_users', methods=['GET'])
def search_users():
    username = request.args.get('username')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({'users': users})

@app.route('/delete_account', methods=['POST'])
def delete_account():
    data = request.get_json()
    username = data.get('username')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({'message': 'Account deleted successfully'})

if __name__ == '__main__':
    app.run()
