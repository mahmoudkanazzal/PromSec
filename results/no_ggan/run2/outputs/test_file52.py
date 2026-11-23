# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'appuser')
    password = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        return redirect('/wrong')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, password FROM usr WHERE username = %s",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            return redirect('/wrong')
        stored_username, stored_password_hash = row
        if check_password_hash(stored_password_hash, password):
            return redirect('/success')
        else:
            return redirect('/wrong')
    except Exception:
        return redirect('/wrong')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()