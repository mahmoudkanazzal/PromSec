import os
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

DB_PATH = 'library.db'
MAX_LENGTH = 255

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT NOT NULL
        )''')

def validate_string(value, field_name):
    if not isinstance(value, str):
        abort(400, description=f'{field_name} must be a string')
    trimmed = value.strip()
    if not trimmed:
        abort(400, description=f'{field_name} cannot be empty')
    if len(trimmed) > MAX_LENGTH:
        abort(400, description=f'{field_name} exceeds maximum length')
    return trimmed

def get_book_by_id(book_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('SELECT id FROM books WHERE id = ?', (book_id,))
        return cur.fetchone()

@app.errorhandler(400)
def handle_400(e):
    return jsonify({'error': e.description if hasattr(e, 'description') else 'Bad Request'}), 400

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': e.description if hasattr(e, 'description') else 'Not Found'}), 404

@app.errorhandler(500)
def handle_500(e):
    return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/add_book', methods=['POST'])
def add_book():
    if not request.is_json:
        abort(400, description='Request body must be JSON')
    data = request.get_json()
    try:
        title = validate_string(data.get('title'), 'title')
        author = validate_string(data.get('author'), 'author')
        genre = validate_string(data.get('genre'), 'genre')
    except Exception as e:
        raise e
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('INSERT INTO books (title, author, genre) VALUES (?, ?, ?)', (title, author, genre))
        book_id = cur.lastrowid
    return jsonify({'message': 'Book added', 'book_id': book_id}), 201

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '').strip()
    pattern = f'%{keyword.lower()}%'
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if keyword:
            cur = conn.execute('SELECT * FROM books WHERE lower(title) LIKE ? OR lower(author) LIKE ?', (pattern, pattern))
        else:
            cur = conn.execute('SELECT * FROM books')
        rows = [dict(row) for row in cur.fetchall()]
    return jsonify(rows), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    if not request.is_json:
        abort(400, description='Request body must be JSON')
    if not get_book_by_id(book_id):
        abort(404, description='Book not found')
    data = request.get_json()
    fields = {}
    if 'title' in data:
        fields['title'] = validate_string(data['title'], 'title')
    if 'author' in data:
        fields['author'] = validate_string(data['author'], 'author')
    if 'genre' in data:
        fields['genre'] = validate_string(data['genre'], 'genre')
    if not fields:
        abort(400, description='No valid fields to update')
    set_clause = ', '.join([f"{k}=?" for k in fields.keys()])
    params = list(fields.values()) + [book_id]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f'UPDATE books SET {set_clause} WHERE id = ?', params)
    return jsonify({'message': 'Book updated'}), 200

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    if not get_book_by_id(book_id):
        abort(404, description='Book not found')
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
    return jsonify({'message': 'Book deleted'}), 200

@app.route('/get_books_by_genre', methods=['GET'])
def get_books_by_genre():
    genre = request.args.get('genre', '').strip()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if genre:
            cur = conn.execute('SELECT * FROM books WHERE genre = ?', (genre,))
        else:
            cur = conn.execute('SELECT * FROM books')
        rows = [dict(row) for row in cur.fetchall()]
    return jsonify(rows), 200

if __name__ == '__main__':
    init_db()
    app.run()