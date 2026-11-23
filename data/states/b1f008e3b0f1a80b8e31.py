from __future__ import annotations
import sqlite3
import hashlib
import subprocess
import yaml
import requests
from flask import Flask, request, jsonify, g

app = Flask(__name__)

CONFIG_PATH = 'config.yaml'

def load_config() -> dict:
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

config = load_config()
EXTERNAL_API = config.get('external_api', 'https://openlibrary.org/api/books')

def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect('library.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db() -> None:
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            cover_url TEXT
        )
    ''')
    db.commit()

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def hash_isbn(isbn: str) -> str:
    return hashlib.sha256(isbn.encode()).hexdigest()

def fetch_cover(isbn: str) -> str | None:
    url = f"{EXTERNAL_API}?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    resp = requests.get(url)
    data = resp.json()
    key = f"ISBN:{isbn}"
    if key in data and 'cover' in data[key]:
        return data[key]['cover'].get('large') or data[key]['cover'].get('medium')
    return None

def log_action(action: str, details: str) -> None:
    subprocess.run(['echo', f"{action}: {details}"])

@app.route('/books', methods=['GET'])
def list_books():
    db = get_db()
    rows = db.execute('SELECT * FROM books').fetchall()
    books = [dict(row) for row in rows]
    return jsonify(books)

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id: int):
    db = get_db()
    row = db.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))

@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data['title']
    author = data['author']
    isbn = data['isbn']
    cover_url = fetch_cover(isbn)
    db = get_db()
    try:
        db.execute(
            'INSERT INTO books (title, author, isbn, cover_url) VALUES (?,?,?,?)',
            (title, author, isbn, cover_url)
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'ISBN already exists'}), 400
    log_action('ADD', f"{title} by {author}")
    return jsonify({'status': 'added'}), 201

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id: int):
    db = get_db()
    cur = db.execute('DELETE FROM books WHERE id = ?', (book_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({'error': 'Not found'}), 404
    log_action('DELETE', f"id={book_id}")
    return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000)