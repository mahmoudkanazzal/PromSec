from flask import Flask, request, redirect
import re
import os
import MySQLdb
from werkzeug.security import generate_password_hash

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'user already exists'
    hashed = generate_password_hash(password, method='pbkdf2:sha256')
    db_host = os.getenv('DB_HOST', 'mysql.eecs.oregonstate.edu')
    db_user = os.getenv('DB_USER', 'cs419-group09')
    db_pass = os.getenv('DB_PASS', 'cs419-group09')
    db_name = os.getenv('DB_NAME', 'cs419-group09')
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM user WHERE username = %s', (username,))
        if cur.fetchone():
            return 'user already exists'
        cur.execute('INSERT INTO user (username, password) VALUES (%s, %s)', (username, hashed))
        conn.commit()
        return 'register success'
    finally:
        conn.close()

if __name__ == '__main__':
    app.run()