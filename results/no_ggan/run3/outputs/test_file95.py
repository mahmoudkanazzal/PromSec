import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret')

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER NOT NULL
            )
        ''')
        conn.commit()

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    if not title or not author or year is None:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        year_int = int(year)
    except (ValueError, TypeError):
        return jsonify({'error': 'Year must be an integer'}), 400
    with get_db_connection() as conn:
        conn.execute(
            'INSERT INTO books (title, author, year) VALUES (?, ?, ?)',
            (title, author, year_int)
        )
        conn.commit()
    return jsonify({'message': 'Book added successfully'}), 201

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    with get_db_connection() as conn:
        rows = conn.execute(
            'SELECT * FROM books WHERE title LIKE ? OR author LIKE ?',
            (pattern, pattern)
        ).fetchall()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    if not title or not author or year is None:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        year_int = int(year)
    except (ValueError, TypeError):
        return jsonify({'error': 'Year must be an integer'}), 400
    with get_db_connection() as conn:
        cur = conn.execute(
            'UPDATE books SET title = ?, author = ?, year = ? WHERE id = ?',
            (title, author, year_int, book_id)
        )
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({'error': 'Book not found'}), 400
    return jsonify({'message': 'Book updated successfully'}), 200

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    with get_db_connection() as conn:
        cur = conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({'error': 'Book not found'}), 400
    return jsonify({'message': 'Book deleted successfully'}), 200

@app.route('/get_books_by_year', methods=['GET'])
def get_books_by_year():
    year = request.args.get('year')
    if not year:
        return jsonify({'error': 'Year parameter is required'}), 400
    try:
        year_int = int(year)
    except ValueError:
        return jsonify({'error': 'Year must be numeric'}), 400
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM books WHERE year = ?', (year_int,)).fetchall()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=False)