import os
import hashlib
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'db')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cur = conn.cursor()
        query = "SELECT * FROM user WHERE username=%s AND password=%s"
        cur.execute(query, (username, password))
        rows = cur.fetchall()
        if rows:
            return "Good Login"
        else:
            return "Bad Login"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()