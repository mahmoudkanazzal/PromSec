import os
import bcrypt
from flask import Flask, request, redirect, abort

app = Flask(__name__)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024

def get_db_connection():
    import pymysql
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400)
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
                row = cur.fetchone()
        if not row:
            return redirect('/', code=302)
        stored_hash = row['password_hash']
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return redirect('/dashboard', code=302)
        return redirect('/', code=302)
    except Exception:
        abort(500)

@app.errorhandler(500)
def internal_error(e):
    return 'Internal Server Error', 500

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host=host, port=port, debug=False)