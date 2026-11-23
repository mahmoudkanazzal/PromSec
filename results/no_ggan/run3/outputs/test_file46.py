from flask import Flask, request
import os
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    conn = MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'appuser'),
        passwd=os.getenv('DB_PASS', ''),
        db=os.getenv('DB_NAME', 'db')
    )
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    if not row:
        return "Bad Login"
    stored_hash = row[0]
    if check_password_hash(stored_hash, password):
        return "Good Login"
    return "Bad Login"

if __name__ == '__main__':
    app.run()