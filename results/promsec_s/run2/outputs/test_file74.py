from flask import Flask, request, redirect
import re, MySQLdb, os, bcrypt

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    if not re.fullmatch(r'[A-Za-z0-9]{3,30}', username):
        return 'Invalid username', 400, {'Content-Type': 'text/plain'}
    if password != confirm_password or not password:
        return 'Passwords do not match', 400, {'Content-Type': 'text/plain'}
    if len(password) > 128:
        return 'Password too long', 400, {'Content-Type': 'text/plain'}
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST', ''),
            user=os.getenv('DB_USER', ''),
            passwd=os.getenv('DB_PASSWORD', ''),
            db=os.getenv('DB_NAME', ''),
            charset='utf8mb4',
            use_unicode=True
        )
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username=%s', (username,))
        if cursor.fetchone():
            return 'Username already exists', 409, {'Content-Type': 'text/plain'}
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, hashed))
        conn.commit()
        return 'Registration successful', 200, {'Content-Type': 'text/plain'}
    except Exception:
        if conn:
            conn.rollback()
        return 'Registration failed', 500, {'Content-Type': 'text/plain'}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()