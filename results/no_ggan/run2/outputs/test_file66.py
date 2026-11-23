import os
import MySQLdb
from flask import Flask, request, redirect
from werkzeug.security import generate_password_hash

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'testuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'test123')
DB_NAME = os.getenv('DB_NAME', 'TESTDB')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/register')
    hashed = generate_password_hash(password)
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', use_unicode=True)
    try:
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT 1 FROM User WHERE username=%s LIMIT 1', (username,))
            if cursor.fetchone():
                return redirect('/register')
            cursor.execute('INSERT INTO User (username, password) VALUES (%s, %s)', (username, hashed))
            conn.commit()
            return redirect('/login')
        finally:
            cursor.close()
    finally:
        conn.close()

if __name__ == '__main__':
    app.run()