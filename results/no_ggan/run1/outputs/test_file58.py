import os
import sys
import hmac
import hashlib
import MySQLdb
from flask import Flask, request, abort, redirect

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'appuser')
    password = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'cwe200')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description="Username and password are required.")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT username, password_hash FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if not row:
            return redirect('/cwe200/')
        stored_username, stored_hash = row
        pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if hmac.compare_digest(pwd_hash, stored_hash):
            return redirect(f"/cwe200/{stored_username}")
        else:
            return redirect('/cwe200/')
    except MySQLdb.Error as e:
        sys.stderr.write(f"{e.args[0]} {e.args[1]}\n")
        abort(500, description="Internal server error.")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)