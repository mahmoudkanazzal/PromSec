import os
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret')

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    year INTEGER NOT NULL
                )
            ''')

init_db()

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    if not isinstance(title, str) or not isinstance(author, str) or not isinstance(year, int):
        return jsonify({'error': 'Invalid input types'}), 400
    try:
        with get_db_connection() as conn:
            with conn:
                conn.execute(
                    'INSERT INTO books (title, author, year) VALUES (?, ?, ?)',
                    (title, author, year)
                )
        return jsonify({'message': 'Book added successfully'}), 201
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

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
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    fields = {}
    if 'title' in data:
        if not isinstance(data['title'], str):
            return jsonify({'error': 'Invalid title type'}), 400
        fields['title'] = data['title']
    if 'author' in data:
        if not isinstance(data['author'], str):
            return jsonify({'error': 'Invalid author type'}), 400
        fields['author'] = data['author']
    if 'year' in data:
        if not isinstance(data['year'], int):
            return jsonify({'error': 'Invalid year type'}), 400
        fields['year'] = data['year']
    if not fields:
        return jsonify({'error': 'No valid fields provided'}), 400
    set_clause = ', '.join([f"{k}=?" for k in fields.keys()])
    params = list(fields.values()) + [book_id]
    try:
        with get_db_connection() as conn:
            with conn:
                cur = conn.execute(f'UPDATE books SET {set_clause} WHERE id=?', params)
                if cur.rowcount == 0:
                    return jsonify({'error': 'Book not found'}), 404
        return jsonify({'message': 'Book updated successfully'}), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        with get_db_connection() as conn:
            with conn:
                cur = conn.execute('DELETE FROM books WHERE id=?', (book_id,))
                if cur.rowcount == 0:
                    return jsonify({'error': 'Book not found'}), 404
        return jsonify({'message': 'Book deleted successfully'}), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/get_books_by_year', methods=['GET'])
def get_books_by_year():
    year_param = request.args.get('year')
    if year_param is None:
        return jsonify({'error': 'Year parameter is required'}), 400
    try:
        year = int(year_param)
    except ValueError:
        return jsonify({'error': 'Year must be an integer'}), 400
    try:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT * FROM books WHERE year=?', (year,)).fetchall()
        result = [dict(row) for row in rows]
        return jsonify(result), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)