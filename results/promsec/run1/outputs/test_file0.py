from flask import Flask, request, redirect
import os, hashlib, MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    salt_bytes = os.urandom(16)
    salt_hex = salt_bytes.hex()
    password_hash = hashlib.sha256(salt_bytes + password.encode('utf-8')).hexdigest()
    db = MySQLdb.connect(host='localhost', user='root', passwd=os.getenv('DB_PASSWORD', ''), db='testdb')
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username=%s LIMIT 1", (username,))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return redirect('/login', code=307)
    cursor.execute("INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)", (username, password_hash, salt_hex))
    db.commit()
    cursor.close()
    db.close()
    return "Registration successful", 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=False)