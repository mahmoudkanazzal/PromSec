from flask import Flask, request, redirect
import MySQLdb
from werkzeug.security import generate_password_hash
import secrets
from os import environ

app = Flask(__name__)

def _process_registration():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/')
    salt = secrets.token_hex(16)
    pwd_hash = generate_password_hash(password, method='pbkdf2:sha256')
    db_host = environ.get('DB_HOST')
    db_user = environ.get('DB_USER')
    db_password = environ.get('DB_PASSWORD')
    db_name = environ.get('DB_NAME')
    if not all([db_host, db_user, db_password, db_name]):
        return redirect('/')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        cursor = conn.cursor()
        sql = "INSERT INTO users (username, password, salt, created_at, updated_at) VALUES (%s, %s, %s, NOW(), NOW())"
        cursor.execute(sql, (username, pwd_hash, salt))
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/')

@app.route('/register', methods=['POST'])
def register_route():
    return _process_registration()

def register():
    return _process_registration()

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False)