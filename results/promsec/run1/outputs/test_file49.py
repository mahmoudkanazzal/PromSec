from flask import Flask, request, redirect
import os
import hashlib
import MySQLdb

app = Flask(__name__)

def _get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    conn = None
    cursor = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE username=%s AND pass=%s"
        cursor.execute(query, (username, password_hash))
        result = cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    if result:
        return redirect('/dashboard')
    else:
        return redirect('/')

if __name__ == '__main__':
    app.run()