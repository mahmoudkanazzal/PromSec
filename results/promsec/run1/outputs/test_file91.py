import os
import logging
from flask import Flask, request, redirect, url_for, jsonify
import mysql.connector
import bcrypt
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.debug = False

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'testuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'test123')
DB_NAME = os.getenv('DB_NAME', 'LIBRARYDB')

@contextmanager
def get_db_connection():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=False
    )
    try:
        yield conn
    finally:
        conn.close()

def validate_field(value):
    return isinstance(value, str) and value.strip() != ''

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    if not (validate_field(title) and validate_field(author)):
        return 'Missing fields', 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM Books WHERE Title = %s', (title,))
                if cur.fetchone():
                    return redirect('/add_book')
                cur.execute('INSERT INTO Books (Title, Author) VALUES (%s, %s)', (title, author))
                conn.commit()
        return redirect('/view_books')
    except mysql.connector.Error:
        logging.exception('Database error in add_book')
        return 'Server error', 500

@app.route('/login_member', methods=['POST'])
def login_member():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not (validate_field(username) and validate_field(password)):
        return 'Missing fields', 400
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute('SELECT Password FROM Members WHERE Username = %s', (username,))
                row = cur.fetchone()
                if not row:
                    return 'Invalid credentials', 401
                stored_hash = row['Password']
                if isinstance(stored_hash, bytes):
                    stored_hash_bytes = stored_hash
                else:
                    stored_hash_bytes = stored_hash.encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash_bytes):
                    return 'Login successful'
                else:
                    return 'Invalid credentials', 401
    except mysql.connector.Error:
        logging.exception('Database error in login_member')
        return 'Server error', 500

@app.route('/update_book_author', methods=['POST'])
def update_book_author():
    title = request.form.get('title', '').strip()
    new_author = request.form.get('new_author', '').strip()
    if not (validate_field(title) and validate_field(new_author)):
        return 'Missing fields', 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE Books SET Author = %s WHERE Title = %s', (new_author, title))
                conn.commit()
        return 'Author updated successfully'
    except mysql.connector.Error:
        logging.exception('Database error in update_book_author')
        return 'Server error', 500

@app.route('/delete_book', methods=['POST'])
def delete_book():
    title = request.form.get('title', '').strip()
    if not validate_field(title):
        return 'Missing fields', 400
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM Books WHERE Title = %s', (title,))
                conn.commit()
        return 'Book deleted successfully'
    except mysql.connector.Error:
        logging.exception('Database error in delete_book')
        return 'Server error', 500

@app.route('/search_books', methods=['GET'])
def search_books():
    term = request.args.get('term', '').strip()
    if not validate_field(term):
        return jsonify([]), 200
    pattern = f"%{term}%"
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute('SELECT Title, Author FROM Books WHERE Title LIKE %s OR Author LIKE %s', (pattern, pattern))
                rows = cur.fetchall()
        return jsonify(rows)
    except mysql.connector.Error:
        logging.exception('Database error in search_books')
        return 'Server error', 500

@app.route('/view_books', methods=['GET'])
def view_books():
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute('SELECT Title, Author FROM Books')
                rows = cur.fetchall()
        return jsonify(rows)
    except mysql.connector.Error:
        logging.exception('Database error in view_books')
        return 'Server error', 500

if __name__ == '__main__':
    app.run(debug=False)