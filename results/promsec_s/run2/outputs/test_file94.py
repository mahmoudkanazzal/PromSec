import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    author = data.get('author')
    if not isinstance(title, str) or not title.strip() or not isinstance(author, str) or not author.strip():
        return jsonify({"error": "Missing title or author"}), 400
    try:
        with get_db_connection() as conn:
            conn.execute('INSERT INTO books (title, author) VALUES (?, ?)', (title.strip(), author.strip()))
            conn.commit()
        return jsonify({"message": "Book added successfully"}), 201
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_book', methods=['GET'])
def get_book():
    book_id = request.args.get('id')
    if not book_id or not book_id.isdigit():
        return jsonify({"error": "Invalid or missing book id"}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,))
            row = cur.fetchone()
        if row is None:
            return jsonify({"error": "Book not found"}), 404
        return jsonify(dict(row)), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_copies', methods=['POST'])
def update_copies():
    data = request.get_json(silent=True) or {}
    book_id = data.get('book_id')
    copies = data.get('copies')
    if not isinstance(book_id, int) or not isinstance(copies, int):
        return jsonify({"error": "Invalid book_id or copies"}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.execute('UPDATE books SET copies = copies + ? WHERE id = ?', (copies, book_id))
            conn.commit()
            if cur.rowcount == 0:
                return jsonify({"error": "Book not found"}), 404
        return jsonify({"message": "Copies updated successfully"}), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_catalog', methods=['GET'])
def get_catalog():
    try:
        with get_db_connection() as conn:
            cur = conn.execute('SELECT title, author, copies FROM books ORDER BY title')
            rows = cur.fetchall()
        catalog = [dict(row) for row in rows]
        return jsonify(catalog), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)