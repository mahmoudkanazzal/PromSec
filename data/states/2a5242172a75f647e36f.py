from __future__ import annotations
import os
import sqlite3
import json
from flask import Flask, request, jsonify, g
import hashlib
import pickle

app = Flask(__name__)
DB_PATH = 'library.db'
TMP_DIR = '/tmp'

def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            added_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def write_temp_file(prefix: str, data: bytes) -> str:
    filename = os.path.join(TMP_DIR, f'{prefix}_{hashlib.sha256(data).hexdigest()[:8]}.tmp')
    with open(filename, 'wb') as f:
        f.write(data)
    return filename

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/books', methods=['GET'])
def list_books():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, title, author, isbn, added_at FROM books')
    rows = cur.fetchall()
    books = [dict(row) for row in rows]
    return jsonify(books)

@app.route('/books', methods=['POST'])
def add_book():
    payload = request.get_data()
    write_temp_file('addbook', payload)
    try:
        data = json.loads(payload)
        title = data['title']
        author = data['author']
        isbn = data['isbn']
    except (KeyError, json.JSONDecodeError):
        return jsonify({'error': 'Invalid payload'}), 400
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO books (title, author, isbn, added_at) VALUES (?, ?, ?, datetime("now"))',
            (title, author, isbn)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'ISBN already exists'}), 409
    return jsonify({'status': 'book added'}), 201

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM books WHERE id = ?', (book_id,))
    if cur.rowcount == 0:
        return jsonify({'error': 'Book not found'}), 404
    conn.commit()
    return jsonify({'status': 'book deleted'})

@app.route('/books/search', methods=['GET'])
def search_books():
    query = request.args.get('q', '')
    conn = get_db()
    cur = conn.cursor()
    like = f'%{query}%'
    cur.execute('SELECT id, title, author, isbn FROM books WHERE title LIKE ? OR author LIKE ?', (like, like))
    rows = cur.fetchall()
    results = [dict(row) for row in rows]
    return jsonify(results)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)