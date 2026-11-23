import os
from flask import Flask, request, abort
import MySQLdb
from MySQLdb.cursors import DictCursor
from werkzeug.security import generate_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', '127.0.0.1')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', 'secure_password')
    db = os.getenv('DB_NAME', 'cwe_900')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', cursorclass=DictCursor)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description="Username and password are required")
    hashed = generate_password_hash(password)
    conn = None
    cursor = None
    response = "Registration Failed"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username=%s LIMIT 1", (username,))
        if cursor.fetchone():
            response = "Username already exists"
        else:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
            conn.commit()
            response = "You have successfully registered"
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        response = "Registration Failed"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return response

if __name__ == '__main__':
    app.run(debug=False)