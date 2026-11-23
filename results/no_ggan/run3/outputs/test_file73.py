import os
import logging
from flask import Flask, request, redirect, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
from MySQLdb.cursors import DictCursor

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'myapp')
    return MySQLdb.connect(host=host, user=user, password=password, database=db, charset='utf8mb4', cursorclass=DictCursor, autocommit=False)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return ('Missing username or password', 400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        pwd_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, pwd_hash))
        conn.commit()
        return redirect('/home')
    except Exception:
        logger.exception('Error during registration')
        if conn:
            conn.rollback()
        return redirect('/home')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return ('Missing username or password', 400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        if not row or not check_password_hash(row['password'], password):
            return ('Invalid credentials', 401)
        return redirect('/dashboard')
    except Exception:
        logger.exception('Error during login')
        return ('Login failed', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/add_book', methods=['POST'])
def add_book():
    book_id = request.form.get('book_id')
    title = request.form.get('title')
    author = request.form.get('author')
    if not book_id or not title or not author:
        return ('Missing book_id, title, or author', 400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO books (book_id, title, author) VALUES (%s, %s, %s)', (book_id, title, author))
        conn.commit()
        return ('Book successfully added', 200)
    except Exception:
        logger.exception('Error adding book')
        if conn:
            conn.rollback()
        return ('Failed to add book', 500)
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
        return ('Missing username or book_id', 400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if not cursor.fetchone():
            return ('User not found', 404)
        cursor.execute('INSERT INTO checkouts (username, book_id) VALUES (%s, %s)', (username, book_id))
        conn.commit()
        return ('Book successfully checked out', 200)
    except Exception:
        logger.exception('Error during checkout')
        if conn:
            conn.rollback()
        return ('Checkout failed', 500)
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
        return ('Missing username or book_id', 400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM checkouts WHERE username = %s AND book_id = %s', (username, book_id))
        if not cursor.fetchone():
            return ('Checkout record not found', 404)
        cursor.execute('DELETE FROM checkouts WHERE username = %s AND book_id = %s', (username, book_id))
        conn.commit()
        return ('Book successfully returned', 200)
    except Exception:
        logger.exception('Error during return')
        if conn:
            conn.rollback()
        return ('Return failed', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/view_books', methods=['GET'])
def view_books():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books')
        rows = cursor.fetchall()
        return jsonify(rows)
    except Exception:
        logger.exception('Error retrieving books')
        return ('Failed to retrieve books', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)