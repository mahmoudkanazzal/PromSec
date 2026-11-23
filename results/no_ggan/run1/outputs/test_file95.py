from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    if not title or not author or not year:
        return jsonify({"error": "Missing required fields"}), 400
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
            (title, author, year)
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"message": "Book added successfully"}), 201

@app.route('/search_books', methods=['GET'])
def search_books():
    keyword = request.args.get('keyword', '')
    pattern = f"%{keyword}%"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ?",
            (pattern, pattern)
        )
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
    finally:
        conn.close()
    return jsonify(result), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    if not title or not author or not year:
        return jsonify({"error": "Missing required fields"}), 400
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE books SET title = ?, author = ?, year = ? WHERE id = ?",
            (title, author, year, book_id)
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"message": "Book updated successfully"}), 200

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"message": "Book deleted successfully"}), 200

@app.route('/get_books_by_year', methods=['GET'])
def get_books_by_year():
    year = request.args.get('year')
    if not year or not year.isdigit():
        return jsonify({"error": "Invalid or missing year parameter"}), 400
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE year = ?", (year,))
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
    finally:
        conn.close()
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=False)