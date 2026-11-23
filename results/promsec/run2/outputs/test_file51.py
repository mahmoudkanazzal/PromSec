import os
from flask import Flask, request, redirect, url_for
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'test')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset='utf8mb4', use_unicode=True)
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, username, password, accesslevel FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    if not row:
        return 'User does not exist'
    if not check_password_hash(row['password'], password):
        return 'Incorrect Password'
    return redirect(url_for('user'))

@app.route('/user')
def user():
    return 'Welcome, user!'

if __name__ == '__main__':
    app.run()