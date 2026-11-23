from flask import Flask, request, jsonify, abort
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json(silent=True)
    if not data or 'title' not in data or 'author' not in data:
        abort(400, description="Missing 'title' or 'author' in request body.")
    title = data['title']
    author = data['author']
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO books (title, author) VALUES (?, ?)', (title, author))
        conn.commit()
    return jsonify({"message": "Book added successfully"}), 201

@app.route('/get_book', methods=['GET'])
def get_book():
    book_id = request.args.get('id')
    if not book_id or not book_id.isdigit():
        abort(400, description="Invalid or missing 'id' query parameter.")
    book_id_int = int(book_id)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM books WHERE id = ?', (book_id_int,))
        row = cur.fetchone()
    if row is None:
        abort(404, description="Book not found.")
    return jsonify(dict(row)), 200

@app.route('/update_copies', methods=['POST'])
def update_copies():
    data = request.get_json(silent=True)
    if not data or 'book_id' not in data or 'copies' not in data:
        abort(400, description="Missing 'book_id' or 'copies' in request body.")
    try:
        book_id = int(data['book_id'])
        copies = int(data['copies'])
    except (ValueError, TypeError):
        abort(400, description="'book_id' and 'copies' must be integers.")
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('UPDATE books SET copies = copies + ? WHERE id = ?', (copies, book_id))
        conn.commit()
    return jsonify({"message": "Copies updated successfully"}), 200

@app.route('/get_catalog', methods=['GET'])
def get_catalog():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT title, author, copies FROM books ORDER BY title')
        rows = cur.fetchall()
    catalog = [dict(row) for row in rows]
    return jsonify(catalog), 200

if __name__ == '__main__':
    app.run(debug=False)