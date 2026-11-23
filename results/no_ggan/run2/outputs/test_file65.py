from flask import Flask, request, redirect
import os
import MySQLdb
from werkzeug.security import generate_password_hash

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return redirect('/')
    pwd_hash = generate_password_hash(password)
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password_db = os.getenv('DB_PASSWORD', '')
    dbname = os.getenv('DB_NAME', 'CWE')
    conn = MySQLdb.connect(host=host, user=user, passwd=password_db, db=dbname)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO User (Username, Password, Email) VALUES (%s, %s, %s)", (username, pwd_hash, username))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()