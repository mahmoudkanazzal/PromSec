from flask import Flask, request, redirect
import hashlib, secrets, os, MySQLdb

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/')
    salt = secrets.token_bytes(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    pwd_hash_hex = pwd_hash.hex()
    salt_hex = salt.hex()
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'Raju')
    db_pass = os.getenv('DB_PASS', 'raju')
    db_name = os.getenv('DB_NAME', 'CWE')
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
    cur = conn.cursor()
    try:
        sql = """INSERT INTO users (username, password, salt, created_at, updated_at)
                 VALUES (%s, %s, %s, NOW(), NOW())"""
        cur.execute(sql, (username, pwd_hash_hex, salt_hex))
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()