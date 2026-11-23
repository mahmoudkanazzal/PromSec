import os
import MySQLdb
from flask import Flask, request
from werkzeug.security import check_password_hash

app = Flask(__name__)

def _get_db_connection():
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASS')
    db = os.getenv('DB_NAME')
    missing = [name for name, val in (('DB_HOST', host), ('DB_USER', user), ('DB_PASS', password), ('DB_NAME', db)) if not val]
    if missing:
        raise RuntimeError('Missing environment variables: ' + ', '.join(missing))
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return 'invalid credentials', 400
    conn = None
    cursor = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username=%s', (username,))
        row = cursor.fetchone()
        if not row:
            return 'invalid credentials', 401
        stored_hash = row[0]
        if check_password_hash(stored_hash, password):
            return 'success'
        return 'invalid credentials', 401
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()