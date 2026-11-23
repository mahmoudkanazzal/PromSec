from flask import Flask, request, jsonify, abort
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def validate_int(value, name):
    try:
        return int(value)
    except (TypeError, ValueError):
        abort(400, description=f"Invalid integer for '{name}'")

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                copies INTEGER NOT NULL DEFAULT 0
            )
        ''')
        conn.commit()

@app.route('/add_book', methods=['POST'])
def add_book():
    if not request.is_json:
        abort(400, description="Request body must be JSON")
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    if title is None or author is None:
        abort(400, description="Missing 'title' or 'author' in request body")
    if not isinstance(title, str) or not isinstance(author, str):
        abort(400, description="'title' and 'author' must be strings")
    with get_db_connection() as conn:
        conn.execute('INSERT INTO books (title, author) VALUES (?, ?)', (title, author))
        conn.commit()
    return jsonify({"message": "Book added successfully"}), 201

@app.route('/get_book', methods=['GET'])
def get_book():
    book_id = request.args.get('id')
    if book_id is None:
        abort(400, description="Missing 'id' query parameter")
    book_id = validate_int(book_id, 'id')
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT id, title, author, copies FROM books WHERE id = ?', (book_id,))
        row = cursor.fetchone()
    if row is None:
        abort(404, description="Book not found")
    return jsonify(dict(row)), 200

@app.route('/update_copies', methods=['POST'])
def update_copies():
    if not request.is_json:
        abort(400, description="Request body must be JSON")
    data = request.get_json()
    book_id = data.get('book_id')
    copies = data.get('copies')
    if book_id is None or copies is None:
        abort(400, description="Missing 'book_id' or 'copies' in request body")
    book_id = validate_int(book_id, 'book_id')
    copies = validate_int(copies, 'copies')
    with get_db_connection() as conn:
        cursor = conn.execute('UPDATE books SET copies = copies + ? WHERE id = ?', (copies, book_id))
        conn.commit()
        if cursor.rowcount == 0:
            abort(404, description="Book not found")
    return jsonify({"message": "Copies updated successfully"}), 200

@app.route('/get_catalog', methods=['GET'])
def get_catalog():
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT title, author, copies FROM books ORDER BY title')
        rows = cursor.fetchall()
    catalog = [dict(row) for row in rows]
    return jsonify(catalog), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=False)