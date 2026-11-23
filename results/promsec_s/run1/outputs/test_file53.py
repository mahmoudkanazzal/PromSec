import os
from flask import Flask, request, Response
import pymysql
import bcrypt

app = Flask(__name__)

def get_db_config():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASS')
    db = os.getenv('DB_NAME')
    missing = [var for var, val in (('DB_USER', user), ('DB_PASS', password), ('DB_NAME', db)) if not val]
    if missing:
        raise RuntimeError('Missing environment variables: ' + ', '.join(missing))
    return {
        'host': host,
        'user': user,
        'password': password,
        'db': db,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': True
    }

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return Response('username and password required', status=400, mimetype='text/plain')
        cfg = get_db_config()
        with pymysql.connect(**cfg) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT password_hash FROM user WHERE username = %s', (username,))
                row = cur.fetchone()
                if not row:
                    return Response('username not found', mimetype='text/plain')
                stored_hash = row['password_hash']
                if isinstance(stored_hash, str):
                    stored_hash = stored_hash.encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    return Response('success', mimetype='text/plain')
                else:
                    return Response('wrong pw', mimetype='text/plain')
    except Exception:
        return Response('internal server error', status=500, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)