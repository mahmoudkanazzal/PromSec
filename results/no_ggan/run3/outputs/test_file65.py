from flask import Flask, request, redirect
import os
import MySQLdb
from werkzeug.security import generate_password_hash

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', '69.195.55.111')
DB_USER = os.getenv('DB_USER', 'ec2-user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'ufo12345')
DB_NAME = os.getenv('DB_NAME', 'CWE')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/')
    password_hash = generate_password_hash(password)
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', use_unicode=True)
    cursor = None
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO User (Username, Password, Email) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, password_hash, username))
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()