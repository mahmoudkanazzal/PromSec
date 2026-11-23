import os
import sqlite3
from flask import Flask, request, jsonify

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise RuntimeError('FLASK_SECRET_KEY environment variable not set')

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    if not all(isinstance(v, str) and v.strip() for v in [title, author, genre]):
        return jsonify({'error': 'title, author, and genre are required strings'}), 400
    try:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO books (title, author, genre) VALUES (?, ?, ?)',
                (title.strip(), author.strip(), genre.strip())
            )
        return jsonify({'message': 'Book added successfully'}), 201
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')
    try:
        with get_db_connection() as conn:
            if keyword:
                pattern = f'%{keyword}%'
                rows = conn.execute(
                    'SELECT * FROM books WHERE title LIKE ? COLLATE NOCASE OR author LIKE ? COLLATE NOCASE',
                    (pattern, pattern)
                ).fetchall()
            else:
                rows = conn.execute('SELECT * FROM books').fetchall()
        result = [dict(row) for row in rows]
        return jsonify(result), 200
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    fields = {}
    for field in ('title', 'author', 'genre'):
        value = data.get(field)
        if value is not None:
            if not isinstance(value, str) or not value.strip():
                return jsonify({'error': f'{field} must be a non‑empty string'}), 400
            fields[field] = value.strip()
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    set_clause = ', '.join(f'{k} = ?' for k in fields)
    params = list(fields.values()) + [book_id]
    try:
        with get_db_connection() as conn:
            cur = conn.execute(f'UPDATE books SET {set_clause} WHERE id = ?', params)
            if cur.rowcount == 0:
                return jsonify({'error': 'Book not found'}), 404
        return jsonify({'message': 'Book updated successfully'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        with get_db_connection() as conn:
            cur = conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
            if cur.rowcount == 0:
                return jsonify({'error': 'Book not found'}), 404
        return jsonify({'message': 'Book deleted successfully'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_books_by_genre', methods=['GET'])
def get_books_by_genre():
    genre = request.args.get('genre')
    if not genre or not isinstance(genre, str) or not genre.strip():
        return jsonify({'error': 'genre query parameter is required'}), 400
    try:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT * FROM books WHERE genre = ?', (genre.strip(),)).fetchall()
        result = [dict(row) for row in rows]
        return jsonify(result), 200
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)