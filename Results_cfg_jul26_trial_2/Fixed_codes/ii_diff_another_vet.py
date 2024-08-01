import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = os.getenv('DB_PATH', 'books.db')

def create_connection():
    return sqlite3.connect(DB_PATH)

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title, author, genre) VALUES (?, ?, ?)", (data['title'], data['author'], data['genre']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book added successfully'})

@app.route('/search_books', methods=['GET'])
def search_books():
    genre = request.args.get('genre')
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE genre=?", (genre,))
    books = cursor.fetchall()
    conn.close()
    return jsonify({'books': books})

@app.route('/update_book/<int:id>', methods=['PUT'])
def update_book(id):
    data = request.get_json()
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE books SET title=?, author=?, genre=? WHERE id=?", (data['title'], data['author'], data['genre'], id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book updated successfully'})

@app.route('/delete_book/<int:id>', methods=['DELETE'])
def delete_book(id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book deleted successfully'})

if __name__ == '__main__':
    app.run()