import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            copies INTEGER NOT NULL DEFAULT 0
        )''')
        conn.commit()
    finally:
        conn.close()

init_db()

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    author = data.get('author')
    if not title or not author:
        return jsonify({'error': 'Missing title or author'}), 400
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO books (title, author) VALUES (?, ?)', (title, author))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'message': 'Book added successfully'}), 201

@app.route('/get_book', methods=['GET'])
def get_book():
    book_id = request.args.get('id')
    if not book_id or not book_id.isdigit():
        return jsonify({'error': 'Invalid or missing id'}), 400
    conn = get_db_connection()
    try:
        cur = conn.execute('SELECT * FROM books WHERE id = ?', (int(book_id),))
        row = cur.fetchone()
    finally:
        conn.close()
    if row is None:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify(dict(row)), 200

@app.route('/update_copies', methods=['POST'])
def update_copies():
    data = request.get_json(silent=True) or {}
    book_id = data.get('book_id')
    copies = data.get('copies')
    try:
        book_id = int(book_id)
        copies = int(copies)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid book_id or copies'}), 400
    conn = get_db_connection()
    try:
        conn.execute('UPDATE books SET copies = copies + ? WHERE id = ?', (copies, book_id))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'message': 'Copies updated successfully'}), 200

@app.route('/get_catalog', methods=['GET'])
def get_catalog():
    conn = get_db_connection()
    try:
        cur = conn.execute('SELECT title, author, copies FROM books ORDER BY title')
        rows = cur.fetchall()
    finally:
        conn.close()
    catalog = [dict(row) for row in rows]
    return jsonify(catalog), 200

if __name__ == '__main__':
    app.run(debug=False)