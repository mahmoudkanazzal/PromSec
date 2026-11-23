import os
from flask import Flask, request, redirect, url_for, jsonify, abort
import MySQLdb
import MySQLdb.cursors
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    password = os.getenv('DB_PASSWORD', 'test123')
    db = os.getenv('DB_NAME', 'LIBRARYDB')
    return MySQLdb.connect(host=host, user=user, password=password, db=db, charset='utf8mb4', cursorclass=MySQLdb.cursors.DictCursor, autocommit=False)

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    if not title or not author:
        abort(400, description='Missing title or author')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM Books WHERE Title = %s', (title,))
        if cur.fetchone():
            return redirect(url_for('add_book'))
        cur.execute('INSERT INTO Books (Title, Author) VALUES (%s, %s)', (title, author))
        conn.commit()
        return redirect(url_for('view_books'))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/login_member', methods=['POST'])
def login_member():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description='Missing username or password')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT password_hash FROM Members WHERE username = %s', (username,))
        row = cur.fetchone()
        if row and check_password_hash(row['password_hash'], password):
            return 'Login successful'
        return 'Invalid credentials', 401
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/update_book_author', methods=['POST'])
def update_book_author():
    title = request.form.get('title')
    new_author = request.form.get('new_author')
    if not title or not new_author:
        abort(400, description='Missing title or new_author')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE Books SET Author = %s WHERE Title = %s', (new_author, title))
        conn.commit()
        return 'Author updated successfully'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/delete_book', methods=['POST'])
def delete_book():
    title = request.form.get('title')
    if not title:
        abort(400, description='Missing title')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM Books WHERE Title = %s', (title,))
        conn.commit()
        return 'Book deleted successfully'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/search_books', methods=['GET'])
def search_books():
    term = request.args.get('term', '')
    pattern = f'%{term}%'
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM Books WHERE Title LIKE %s OR Author LIKE %s', (pattern, pattern))
        rows = cur.fetchall()
        return jsonify(rows)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/view_books', methods=['GET'])
def view_books():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM Books')
        rows = cur.fetchall()
        return jsonify(rows)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)