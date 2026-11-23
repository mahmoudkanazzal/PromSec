import os
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default')

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    year INTEGER NOT NULL
                )
            ''')

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    if not isinstance(title, str) or not isinstance(author, str) or not isinstance(year, int):
        return jsonify({'error': 'Missing or invalid fields'}), 400
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO books (title, author, year) VALUES (?, ?, ?)', (title, author, year))
    return jsonify({'message': 'Book added successfully'}), 201

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword.lower()}%'
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id, title, author, year FROM books WHERE lower(title) LIKE ? OR lower(author) LIKE ?', (pattern, pattern))
            rows = cur.fetchall()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    fields = {}
    if 'title' in data:
        if not isinstance(data['title'], str):
            return jsonify({'error': 'Invalid title'}), 400
        fields['title'] = data['title']
    if 'author' in data:
        if not isinstance(data['author'], str):
            return jsonify({'error': 'Invalid author'}), 400
        fields['author'] = data['author']
    if 'year' in data:
        if not isinstance(data['year'], int):
            return jsonify({'error': 'Invalid year'}), 400
        fields['year'] = data['year']
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    set_clause = ', '.join([f"{k}=?" for k in fields.keys()])
    params = list(fields.values()) + [book_id]
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f'UPDATE books SET {set_clause} WHERE id=?', params)
            if cur.rowcount == 0:
                return jsonify({'error': 'Book not found'}), 404
    return jsonify({'message': 'Book updated successfully'}), 200

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM books WHERE id=?', (book_id,))
            if cur.rowcount == 0:
                return jsonify({'error': 'Book not found'}), 404
    return jsonify({'message': 'Book deleted successfully'}), 200

@app.route('/get_books_by_year', methods=['GET'])
def get_books_by_year():
    year = request.args.get('year')
    if year is None:
        return jsonify({'error': 'Year parameter is required'}), 400
    try:
        year_int = int(year)
    except ValueError:
        return jsonify({'error': 'Year must be an integer'}), 400
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id, title, author, year FROM books WHERE year=?', (year_int,))
            rows = cur.fetchall()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=False)