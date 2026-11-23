from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os
import secrets

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form['username']
        password = request.form['password']
    except Exception:
        return 'Invalid input', 400
    salt_bytes = secrets.token_bytes(16)
    salt_hex = salt_bytes.hex()
    password_hash = hashlib.sha256(salt_bytes + password.encode('utf-8')).hexdigest()
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    try:
        with MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1 FROM users WHERE username=%s LIMIT 1', (username,))
                if cursor.fetchone():
                    return redirect('/login', code=307)
                cursor.execute('INSERT INTO users (username,password,salt,account_created) VALUES (%s,%s,%s,%s)', (username, password_hash, salt_hex, 1))
            conn.commit()
        return 'Registration successful', 201
    except MySQLdb.Error:
        print('Database error occurred')
        return 'Internal server error', 500
    except Exception:
        print('Unexpected error occurred')
        return 'Internal server error', 500

if __name__ == '__main__':
    app.run()