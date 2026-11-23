from flask import Flask, request, redirect
import os
import hashlib
import MySQLdb

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'Raju')
    passwd = os.getenv('DB_PASSWORD', 'raju')
    db = os.getenv('DB_NAME', 'CWE')
    return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset='utf8mb4')

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/')
    salt_bytes = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, 100000)
    salt_hex = salt_bytes.hex()
    hash_hex = hash_bytes.hex()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO users (username, password, salt, created_at, updated_at)
                 VALUES (%s, %s, %s, NOW(), NOW())"""
        cursor.execute(sql, (username, hash_hex, salt_hex))
        conn.commit()
    finally:
        if conn:
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()