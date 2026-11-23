from flask import Flask, request
import os
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

def _get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'root')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return "Bad Login"
    conn = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        row = cursor.fetchone()
        cursor.close()
        if row and check_password_hash(row['password'], password):
            return "Good Login"
        return "Bad Login"
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()