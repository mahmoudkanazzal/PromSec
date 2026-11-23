from flask import Flask, request
import os
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'appuser'),
        passwd=os.getenv('DB_PASSWORD', ''),
        db=os.getenv('DB_NAME', 'db'),
        charset='utf8mb4',
        use_unicode=True
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT passwort FROM userdaten WHERE username=%s', (username,))
            row = cursor.fetchone()
            if row and check_password_hash(row[0], password):
                return 'Eingeloggt'
            else:
                return 'Falscher Benutzername oder Passwort'
        finally:
            cursor.close()
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)