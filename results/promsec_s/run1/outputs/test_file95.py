import os
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

DB_PATH = 'library.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year INTEGER NOT NULL
            )
        ''')

def dict_from_row(row):
    return {'id': row[0], 'title': row[1], 'author': row[2], 'year': row[3]}

def validate_book_data(data, partial=False):
    if not isinstance(data, dict):
        abort(400, description='Invalid JSON payload')
    fields = {}
    if not partial or 'title' in data:
        title = data.get('title')
        if not isinstance(title, str) or not title.strip():
            abort(400, description='Title must be a non‑empty string')
        fields['title'] = title.strip()
    if not partial or 'author' in data:
        author = data.get('author')
        if not isinstance(author, str) or not author.strip():
            abort(400, description='Author must be a non‑empty string')
        fields['author'] = author.strip()
    if not partial or 'year' in data:
        year = data.get('year')
        if not isinstance(year, int):
            abort(400, description='Year must be an integer')
        fields['year'] = year
    if not fields:
        abort(400, description='No valid fields provided')
    return fields

@app.errorhandler(400)
def handle_400(e):
    return jsonify(error=str(e.description)), 400

@app.errorhandler(404)
def handle_404(e):
    return jsonify(error='Resource not found'), 404

@app.errorhandler(500)
def handle_500(e):
    return jsonify(error='Internal server error'), 500

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if data is None:
        abort(400, description='Missing JSON payload')
    fields = validate_book_data(data)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            'INSERT INTO books (title, author, year) VALUES (?, ?, ?)',
            (fields['title'], fields['author'], fields['year'])
        )
    return jsonify(message='Book added successfully'), 201

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword')
    if not keyword:
        abort(400, description='Keyword query parameter is required')
    pattern = f'%{keyword}%'
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            'SELECT * FROM books WHERE title LIKE ? COLLATE NOCASE OR author LIKE ? COLLATE NOCASE',
            (pattern, pattern)
        )
        rows = cur.fetchall()
    result = [dict_from_row(row) for row in rows]
    return jsonify(result), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    if data is None:
        abort(400, description='Missing JSON payload')
    fields = validate_book_data(data, partial=True)
    set_clause = ', '.join([f"{k}=?" for k in fields.keys()])
    values = list(fields.values())
    values.append(book_id)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(f'UPDATE books SET {set_clause} WHERE id=?', values)
        if cur.rowcount == 0:
            abort(404, description='Book not found')
    return jsonify(message='Book updated successfully'), 200

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('DELETE FROM books WHERE id=?', (book_id,))
        if cur.rowcount == 0:
            abort(404, description='Book not found')
    return jsonify(message='Book deleted successfully'), 200

@app.route('/get_books_by_year', methods=['GET'])
def get_books_by_year():
    year_param = request.args.get('year')
    if year_param is None:
        abort(400, description='Year query parameter is required')
    try:
        year = int(year_param)
    except ValueError:
        abort(400, description='Year must be an integer')
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute('SELECT * FROM books WHERE year=?', (year,))
        rows = cur.fetchall()
    result = [dict_from_row(row) for row in rows]
    return jsonify(result), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=False)