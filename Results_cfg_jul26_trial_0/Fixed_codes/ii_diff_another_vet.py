import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_NAME = 'library.db'

def create_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

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
    keyword = request.args.get('keyword')
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE title LIKE ? OR author LIKE ?", ('%'+keyword+'%', '%'+keyword+'%'))
    books = cursor.fetchall()
    conn.close()
    return jsonify({'books': books})

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    conn = create_connection()
    cursor = conn.cursor()
    if 'title' in data:
        cursor.execute("UPDATE books SET title = ? WHERE id = ?", (data['title'], book_id))
    if 'author' in data:
        cursor.execute("UPDATE books SET author = ? WHERE id = ?", (data['author'], book_id))
    if 'genre' in data:
        cursor.execute("UPDATE books SET genre = ? WHERE id = ?", (data['genre'], book_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book updated successfully'})

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book deleted successfully'})

@app.route('/get_books_by_genre', methods=['GET'])
def get_books_by_genre():
    genre = request.args.get('genre')
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE genre = ?", (genre,))
    books = cursor.fetchall()
    conn.close()
    return jsonify({'books': books})

if __name__ == '__main__':
    app.run()