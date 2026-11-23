from flask import Flask, request, redirect, abort
import os
import hashlib
import MySQLdb

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
        return "Missing username or password", 400
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, accesslevel FROM user WHERE username = %s", (username,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    if not row:
        return "User does not exist", 404
    stored_hash = row[2]
    computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    if computed_hash != stored_hash:
        return "Incorrect Password", 401
    return redirect('/user', code=302)

if __name__ == "__main__":
    app.run()