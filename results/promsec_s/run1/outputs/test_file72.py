from flask import Flask, request, redirect
import os
import re
import logging
from werkzeug.security import generate_password_hash
import MySQLdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_]{3,30}$')

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/home')
    if not USERNAME_PATTERN.match(username):
        return redirect('/home')
    if len(password) > 256:
        return redirect('/home')
    password_hash = generate_password_hash(password)
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(
            host='localhost',
            user='root',
            passwd=os.getenv('DB_PASSWORD', ''),
            db='mysite',
            charset='utf8mb4',
            use_unicode=True
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user (username, password) VALUES (%s, %s)",
            (username, password_hash)
        )
        conn.commit()
    except Exception:
        logger.exception('Error during user registration')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/home')

if __name__ == '__main__':
    app.run()