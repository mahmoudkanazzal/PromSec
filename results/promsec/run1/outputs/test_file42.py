import os
from flask import Flask, request, Response
import mysql.connector
from werkzeug.security import generate_password_hash

app = Flask(__name__)

def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', ''),
        user=os.getenv('DB_USER', ''),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', ''),
        autocommit=False
    )
    return conn

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return Response('Missing required fields', status=400, mimetype='text/plain')
    password_hash = generate_password_hash(password)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
                if cursor.fetchone():
                    conn.rollback()
                    return Response('Username already exists', status=400, mimetype='text/plain')
                cursor.execute(
                    'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
                    (username, password_hash)
                )
                conn.commit()
                return Response('User registered successfully', status=200, mimetype='text/plain')
            except Exception:
                conn.rollback()
                raise
    except Exception:
        return Response('Registration failed', status=500, mimetype='text/plain')

@app.route('/checkout', methods=['POST'])
def checkout():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        return Response('Missing required fields', status=400, mimetype='text/plain')
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
                if not cursor.fetchone():
                    conn.rollback()
                    return Response('User not found', status=400, mimetype='text/plain')
                cursor.execute(
                    'INSERT INTO checkouts (username, book_id) VALUES (%s, %s)',
                    (username, book_id)
                )
                conn.commit()
                return Response('Checkout successful', status=200, mimetype='text/plain')
            except Exception:
                conn.rollback()
                raise
    except Exception:
        return Response('Checkout failed', status=500, mimetype='text/plain')

@app.route('/return', methods=['POST'])
def return_book():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        return Response('Missing required fields', status=400, mimetype='text/plain')
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'SELECT 1 FROM checkouts WHERE username = %s AND book_id = %s',
                    (username, book_id)
                )
                if not cursor.fetchone():
                    conn.rollback()
                    return Response('Checkout record not found', status=400, mimetype='text/plain')
                cursor.execute(
                    'DELETE FROM checkouts WHERE username = %s AND book_id = %s',
                    (username, book_id)
                )
                conn.commit()
                return Response('Return successful', status=200, mimetype='text/plain')
            except Exception:
                conn.rollback()
                raise
    except Exception:
        return Response('Return failed', status=500, mimetype='text/plain')

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    app.run(host=host, port=port, debug=False)