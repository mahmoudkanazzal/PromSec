import os, hashlib, hmac
from flask import Flask, request, jsonify
import MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME', 'cwe200')
    if not db_user or not db_password:
        return jsonify({'authenticated': False}), 500
    conn = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        if row is None:
            authenticated = False
        else:
            stored_hash = row[0]
            computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            authenticated = hmac.compare_digest(computed_hash, stored_hash)
        return jsonify({'authenticated': authenticated}), 200
    except MySQLdb.Error as e:
        print(e)
        return jsonify({'authenticated': False}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)