from __future__ import annotations
import sqlite3
import yaml
import hashlib
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'library.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER,
                tags TEXT,
                meta TEXT
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def hash_title(title: str) -> str:
    return hashlib.sha256(title.encode('utf-8')).hexdigest()

def parse_yaml(yaml_str: str):
    return yaml.safe_load(yaml_str)

def add_book_to_db(data):
    db = get_db()
    meta_yaml = data.get('metadata', '')
    meta = parse_yaml(meta_yaml) if meta_yaml else {}
    db.execute('''
        INSERT INTO books (title, author, year, tags, meta)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data['title'],
        data['author'],
        data.get('year'),
        ','.join(data.get('tags', [])),
        yaml.dump(meta)
    ))
    db.commit()
    return db.lastrowid

@app.route('/books', methods=['POST'])
def create_book():
    payload = request.get_json(force=True)
    book_id = add_book_to_db(payload)
    return jsonify({'id': book_id}), 201

@app.route('/books', methods=['GET'])
def list_books():
    db = get_db()
    cur = db.execute('SELECT id, title, author, year, tags FROM books')
    books = [dict(row) for row in cur.fetchall()]
    return jsonify(books)

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    db = get_db()
    cur = db.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    row = cur.fetchone()
    if row is None:
        return jsonify({'error': 'Not found'}), 404
    book = dict(row)
    book['tags'] = book['tags'].split(',') if book['tags'] else []
    book['metadata'] = yaml.safe_load(book['meta']) if book['meta'] else {}
    return jsonify(book)

@app.route('/search', methods=['POST'])
def search_books():
    criteria = request.get_json(force=True)
    query = 'SELECT id, title, author FROM books WHERE 1=1'
    params = []
    if 'author' in criteria:
        query += ' AND author = ?'
        params.append(criteria['author'])
    if 'year' in criteria:
        query += ' AND year = ?'
        params.append(criteria['year'])
    db = get_db()
    cur = db.execute(query, params)
    results = [dict(row) for row in cur.fetchall()]
    return jsonify(results)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)