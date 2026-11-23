import os
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'mysql.eecs.oregonstate.edu')
    user = os.getenv('DB_USER', 'cs419-group09')
    password = os.getenv('DB_PASS', 'cs419-group09')
    db = os.getenv('DB_NAME', 'cs419-group09')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify(error="Username and password are required"), 400
    hashed = generate_password_hash(password)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify(error="User already exists"), 409
        cursor.execute("INSERT INTO user (username, password) VALUES (%s, %s)", (username, hashed))
        conn.commit()
        return jsonify(message="Register success"), 201
    except MySQLdb.Error:
        return jsonify(error="Database error"), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    app.run()