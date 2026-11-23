import os
import logging
from flask import Flask, request, redirect
import MySQLdb
from werkzeug.security import generate_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'cisco123')
    db = os.getenv('DB_NAME', 'mysite')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        logger.warning('Missing username or password in registration attempt')
        return redirect('/home')
    hashed_password = generate_password_hash(password)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = 'INSERT INTO user (username, password) VALUES (%s, %s)'
        cursor.execute(sql, (username, hashed_password))
        conn.commit()
        logger.info('User registered: %s', username)
        return redirect('/home')
    except MySQLdb.Error as e:
        logger.error('Database error during registration: %s', e)
        return redirect('/home')
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    app.run()