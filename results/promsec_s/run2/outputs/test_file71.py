import os, secrets, hashlib, MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'Raju')
DB_PASS = os.getenv('DB_PASS', 'raju')
DB_NAME = os.getenv('DB_NAME', 'CWE')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/')
    salt = secrets.token_bytes(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cursor = conn.cursor()
        sql = """INSERT INTO users (username, password, salt, created_at, updated_at)
                 VALUES (%s, %s, %s, NOW(), NOW())"""
        cursor.execute(sql, (username, pwd_hash, salt))
        conn.commit()
    except MySQLdb.Error:
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()