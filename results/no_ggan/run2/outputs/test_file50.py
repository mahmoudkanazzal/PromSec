from flask import Flask, request
import os
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return "Wrong Username"
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT password FROM user WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if not row:
            return "Wrong Username"
        stored_hash = row[0]
        if check_password_hash(stored_hash, password):
            return "Login Success"
        else:
            return "Wrong Password"
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()