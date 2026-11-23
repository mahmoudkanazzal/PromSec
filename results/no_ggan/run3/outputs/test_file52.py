import os
import hashlib
import MySQLdb
from flask import Flask, request, redirect
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASS', 'root')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return redirect('/wrong')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM usr WHERE username = %s", (username,))
        row = cur.fetchone()
    except MySQLdb.Error:
        return redirect('/wrong')
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass
    if not row:
        return redirect('/wrong')
    stored_hash = row[0]
    if check_password_hash(stored_hash, password):
        return redirect('/success')
    return redirect('/wrong')

if __name__ == '__main__':
    app.run()