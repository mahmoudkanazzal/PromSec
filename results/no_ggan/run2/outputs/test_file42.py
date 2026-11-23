import os
from flask import Flask, request, abort, make_response
import MySQLdb
from werkzeug.security import generate_password_hash

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_USER = os.getenv('DB_USER', 'app_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'secure_password')
DB_NAME = os.getenv('DB_NAME', 'library_db')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', use_unicode=True)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description='Username and password are required')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return make_response('Username already exists', 409)
        password_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))
        conn.commit()
        return make_response('You have successfully registered', 201)
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return make_response('Registration Failed', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/checkout', methods=['POST'])
def checkout():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        abort(400, description='Username and book_id are required')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if not cursor.fetchone():
            return make_response('User not found', 404)
        cursor.execute('INSERT INTO checkouts (username, book_id, checkout_date) VALUES (%s, %s, NOW())', (username, book_id))
        conn.commit()
        return make_response('Book successfully checked out', 200)
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return make_response('Checkout Failed', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/return', methods=['POST'])
def return_book():
    username = request.form.get('username')
    book_id = request.form.get('book_id')
    if not username or not book_id:
        abort(400, description='Username and book_id are required')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM checkouts WHERE username = %s AND book_id = %s', (username, book_id))
        if not cursor.fetchone():
            return make_response('Checkout record not found', 404)
        cursor.execute('DELETE FROM checkouts WHERE username = %s AND book_id = %s', (username, book_id))
        conn.commit()
        return make_response('Book successfully returned', 200)
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return make_response('Return Failed', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)