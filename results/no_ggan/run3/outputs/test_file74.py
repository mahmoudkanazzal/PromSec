# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request
import os
import bcrypt
import MySQLdb
import MySQLdb.cursors

app = Flask(__name__)

def _get_db_connection():
    host = os.getenv('DB_HOST', '127.0.0.1')
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASSWORD', 'password')
    db = os.getenv('DB_NAME', 'cwe_900')
    return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db,
                           charset='utf8mb4',
                           cursorclass=MySQLdb.cursors.DictCursor,
                           autocommit=False)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    if not username or not password:
        return "Username and password are required", 400
    if password != confirm_password:
        return "Passwords do not match", 400
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cnx = None
    try:
        cnx = _get_db_connection()
        with cnx.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return "Username already exists", 409
            cur.execute("INSERT INTO users (username, pw_hash) VALUES (%s, %s)", (username, pw_hash))
        cnx.commit()
        return "You have successfully registered", 201
    except MySQLdb.Error:
        if cnx:
            cnx.rollback()
        return "Registration Failed", 500
    finally:
        if cnx:
            cnx.close()

if __name__ == '__main__':
    app.run()