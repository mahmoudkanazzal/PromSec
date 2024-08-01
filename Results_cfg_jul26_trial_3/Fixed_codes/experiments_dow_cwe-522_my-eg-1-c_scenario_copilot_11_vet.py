import os
from flask import Flask, request, jsonify
import bcrypt
import mysql.connector

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_DATABASE = os.getenv('DB_DATABASE', 'cwe_900')

def connect_to_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )

def register():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not username or not password or not confirm_password:
        return jsonify({'message': 'Missing username, password, or confirm_password'}), 400

    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        db = connect_to_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            return jsonify({'message': 'Username already exists'}), 400

        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        db.commit()

        return jsonify({'message': 'Registration successful'}), 200

    except mysql.connector.Error as err:
        return jsonify({'message': f'Database error: {err}'}), 500

    finally:
        cursor.close()
        db.close()

@app.route('/register', methods=['POST'])
def register_endpoint():
    return register()

if __name__ == '__main__':
    app.run()