import os
import MySQLdb
from flask import Flask, request
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    passwd = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return 'invalid credentials', 400
    try:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            try:
                cur.execute('SELECT password FROM users WHERE username=%s', (username,))
                row = cur.fetchone()
            finally:
                cur.close()
        finally:
            conn.close()
    except MySQLdb.Error:
        return 'internal error', 500
    if not row:
        return 'invalid credentials', 401
    stored_hash = row[0]
    if check_password_hash(stored_hash, password):
        return 'success'
    return 'invalid credentials', 401

if __name__ == '__main__':
    # In production, use a WSGI server instead of Flask's built-in server.
    app.run()