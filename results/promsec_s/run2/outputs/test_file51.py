from flask import Flask, request, redirect
import os, hashlib, hmac, pymysql

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, username, password, accesslevel FROM user WHERE username = %s", (username,))
                row = cur.fetchone()
        finally:
            conn.close()
    except Exception:
        return 'Internal server error', 500
    if not row:
        return 'User does not exist'
    stored_hash = row['password']
    submitted_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    if not hmac.compare_digest(submitted_hash, stored_hash):
        return 'Incorrect Password'
    return redirect('/user', code=302)

if __name__ == '__main__':
    app.run()