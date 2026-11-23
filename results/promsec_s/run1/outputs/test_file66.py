import os
import re
import logging
from contextlib import closing
from flask import Flask, request, redirect
import pymysql
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not re.fullmatch(r'\w{3,30}', username):
        return 'Invalid username', 400
    if len(password) < 8:
        return 'Password too short', 400
    pwd_hash = generate_password_hash(password, method='pbkdf2:sha256')
    try:
        with closing(pymysql.connect(host=db_host,
                                    user=db_user,
                                    password=db_password,
                                    database=db_name,
                                    cursorclass=pymysql.cursors.DictCursor)) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
                if cur.fetchone():
                    return redirect('./register')
                cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pwd_hash))
            conn.commit()
        return redirect('./login')
    except pymysql.MySQLError as e:
        logger.error(e)
        return 'Internal server error', 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)