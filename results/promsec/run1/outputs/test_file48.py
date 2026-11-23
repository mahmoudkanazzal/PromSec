from __future__ import print_function
import os
from flask import Flask, request, jsonify
import MySQLdb
from werkzeug.security import check_password_hash

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', '')
DB_NAME = os.getenv('DB_NAME', 'test')

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json(force=True)
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({'message': 'Falscher Benutzername oder Passwort'}), 400
        conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, charset='utf8', use_unicode=True)
        try:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT password FROM userdaten WHERE username=%s", (username,))
                row = cursor.fetchone()
                if not row:
                    return jsonify({'message': 'Falscher Benutzername oder Passwort'}), 401
                stored_hash = row[0]
                if check_password_hash(stored_hash, password):
                    return jsonify({'message': 'Eingeloggt'}), 200
                else:
                    return jsonify({'message': 'Falscher Benutzername oder Passwort'}), 401
            finally:
                cursor.close()
        finally:
            conn.close()
    except Exception:
        return jsonify({'message': 'Ein Fehler ist aufgetreten'}), 500

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    app.run(host=host, port=port, debug=False)