from flask import Flask, request, redirect, abort
import os
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return "Missing username or password", 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT id, username, password, accesslevel FROM user WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
    except MySQLdb.Error:
        return "Database error", 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    if not row:
        return "User does not exist", 404
    stored_hash = row[2]
    if not check_password_hash(stored_hash, password):
        return "Incorrect Password", 401
    return redirect('/user', code=302)

if __name__ == '__main__':
    app.run()