from flask import Flask, request, redirect
import os
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'app_user'),
        passwd=os.getenv('DB_PASS', ''),
        db=os.getenv('DB_NAME', 'db')
    )
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM user_info WHERE username = %s", (username,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    if row and check_password_hash(row[0], password):
        return redirect('/')
    return redirect('/error')

if __name__ == '__main__':
    app.run()